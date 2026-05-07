import sounddevice as sd
import whisper
import numpy as np
import threading
import queue
import os
import warnings
from difflib import SequenceMatcher
import string

brew_bin = "/opt/homebrew/bin"
current_path = os.environ.get("PATH", "")
if not current_path.startswith(brew_bin + ":"):
    os.environ["PATH"] = f"{brew_bin}:{current_path}"

import speech_recognition as sr

# from google.cloud import speech

# Thread-safe queue for audio chunks
audio_queue = queue.Queue()
response = ""
processing_thread = None
stop_recording = threading.Event()
stop_processing = threading.Event()  # NEW: Signal to stop processing thread


def audio_callback(indata, frames, time, status):
    audio_queue.put(indata.copy())


def record_audio_stream(fs=16000, blocksize=4096):
    global stop_recording
    stop_recording.clear()

    with sd.InputStream(
        callback=audio_callback, channels=1, samplerate=fs, blocksize=blocksize
    ):
        print("Recording... Press Ctrl+C to stop.")
        stop_recording.wait()


def is_similar(a, b, threshold=0.8):
    """Check if two strings are similar enough"""
    # Remove punctuation and normalize
    a_clean = a.translate(str.maketrans("", "", string.punctuation)).lower()
    b_clean = b.translate(str.maketrans("", "", string.punctuation)).lower()

    result = SequenceMatcher(None, a_clean, b_clean).ratio() >= threshold
    print(f"Comparing '{a_clean}' and '{b_clean}': {result}")
    return result


def get_word_combinations(text):
    """Generate all individual words and consecutive word combinations"""
    words = text.split()
    combinations = []

    # Add individual words
    combinations.extend(words)

    # Add consecutive word combinations (2-word, 3-word, etc.)
    for n in range(2, len(words) + 1):
        for i in range(len(words) - n + 1):
            combination = " ".join(words[i : i + n])
            combinations.append(combination)

    return combinations


def process_audio_stream(model):
    global stop_processing
    try:
        print("Processing thread started.")
        speech_text = ""
        while not stop_processing.is_set():  # FIX: Check stop signal
            try:
                # Use timeout to allow checking stop_processing
                audio_chunk = audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            audio_chunk = audio_chunk.flatten().astype(np.float32)

            max_val = np.max(np.abs(audio_chunk))
            if max_val < 0.01:
                continue

            audio_chunk = audio_chunk / max_val

            result = model.transcribe(audio_chunk, language="en", word_timestamps=True)
            speech_text = result["text"].strip()

            if "segments" in result and result["segments"]:
                no_speech_prob = result["segments"][0].get("no_speech_prob", 0)
                if no_speech_prob > 0.8:
                    print("No speech detected in segment, skipping...")
                    continue

            if "bono" in speech_text.lower() or any(
                map(
                    lambda word: is_similar("bono", word),
                    (get_word_combinations(speech_text) if speech_text else []),
                )
            ):
                print("Chef Bono detected in speech!\n")
                speech_text = ""
                listen_for_bono(stop_word="chef", model=model)

    except Exception as e:
        print(f"Error in processing thread: {e}")
        stop_recording.set()
    finally:
        # Cleanup
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
            except queue.Empty:
                break


def listen_for_bono(stop_word="chef", model=None):
    global response, stop_recording, audio_queue
    stop_word = stop_word.lower()

    recognizer = sr.Recognizer()

    print(f"Listening... say '{stop_word}' to exit.")

    buffer = []
    normalized = ""
    sample_rate = 16000

    while True:
        try:
            audio_chunk = audio_queue.get(timeout=0.5)
            buffer.append(audio_chunk)

            if len(buffer) >= 4:  # INCREASED from 1
                full_audio = np.concatenate(buffer, axis=0)
                full_audio = full_audio.flatten().astype(np.float32)

                max_val = np.max(np.abs(full_audio))
                print(f"Audio level: {max_val}")  # DEBUG: See audio levels

                if max_val > 0.01:
                    full_audio = full_audio / max_val

                    # Convert to int16 for sr.AudioData
                    full_audio_int16 = (full_audio * 32767).astype(np.int16)

                    audio_data = sr.AudioData(
                        full_audio_int16.tobytes(), sample_rate, 2
                    )

                    try:
                        # print("Sending to Google API...")
                        text = recognizer.recognize_google(audio_data).lower()
                        print(text, end=" ")
                        normalized += text + " "

                        if stop_word in normalized:
                            print("Stop word detected. Exiting.")
                            response = normalized
                            stop_recording.set()
                            break
                    except sr.UnknownValueError:
                        print("Could not understand audio")
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")

                buffer = []  # Reset for next chunk

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in listen_for_bono: {e}")
            break


def initialize_model():
    print("Model is loading...")
    model = whisper.load_model("base")

    # print("Warming up model...")
    dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
    try:
        model.transcribe(dummy_audio, language="en")
    except:
        pass  # Ignore errors on warmup
    print("Model ready!")

    return model


def listen(model):
    global audio_queue, stop_recording, response, processing_thread, stop_processing

    # Reset global state
    response = ""
    stop_recording.clear()
    stop_processing.clear()  # FIX: Clear stop signal

    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break

    # Start processing thread
    processing_thread = threading.Thread(
        target=process_audio_stream, args=(model,), daemon=True
    )
    processing_thread.start()

    # Start recording (main thread blocks here)
    record_audio_stream()

    # Signal processing thread to stop
    stop_processing.set()  # FIX: Tell thread to exit

    # Give the processing thread a moment to finish
    processing_thread.join(timeout=2)

    return response


if __name__ == "__main__":
    warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")
    stt_model = initialize_model()

    while True:
        print("go")
        listen(stt_model)
