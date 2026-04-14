import sounddevice as sd
import whisper
import numpy as np
import threading
import queue
import os

brew_bin = "/opt/homebrew/bin"
current_path = os.environ.get("PATH", "")
if not current_path.startswith(brew_bin + ":"):
    os.environ["PATH"] = f"{brew_bin}:{current_path}"

import speech_recognition as sr

# Thread-safe queue for audio chunks
audio_queue = queue.Queue()
response = ""
processing_thread = None
stop_recording = threading.Event()
stop_processing = threading.Event()  # NEW: Signal to stop processing thread


def audio_callback(indata, frames, time, status):
    audio_queue.put(indata.copy())


def record_audio_stream(fs=16000, blocksize=16000):
    global stop_recording
    stop_recording.clear()

    with sd.InputStream(
        callback=audio_callback, channels=1, samplerate=fs, blocksize=blocksize
    ):
        print("Recording... Press Ctrl+C to stop.")
        stop_recording.wait()


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
                if no_speech_prob > 0.5:
                    continue

            if "bono" in speech_text.lower():
                print("Chef Bono detected in speech!\n")
                speech_text = ""
                listen_for_bono(stop_word="chef")

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


def listen_for_bono(stop_word="chef"):
    global response
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    stop_word = stop_word.lower()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print(f"Listening... say '{stop_word}' to exit.")

        while True:
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=6)
                text = recognizer.recognize_google(audio)
                normalized = text.lower()

                if stop_word in normalized:
                    print(text)
                    print("Stop word detected. Exiting.")
                    response = text
                    stop_recording.set()
                    break

            except sr.WaitTimeoutError:
                print("No speech detected (timeout). Try again...")
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                break


def initialize_model():
    print("Model is loading...")
    model = whisper.load_model("base")
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
