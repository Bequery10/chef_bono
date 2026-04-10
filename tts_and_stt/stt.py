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


def audio_callback(indata, frames, time, status):
    # indata shape: (frames, channels)
    audio_queue.put(indata.copy())


stop_recording = threading.Event()


def record_audio_stream(fs=16000, blocksize=16000):
    global stop_recording
    stop_recording.clear()  # Reset flag

    with sd.InputStream(
        callback=audio_callback, channels=1, samplerate=fs, blocksize=blocksize
    ):
        print("Recording... Press Ctrl+C to stop.")
        stop_recording.wait()  # Waits until stop_recording.set() is called


def process_audio_stream(model):
    try:
        print("Processing thread started.")
        speech_text = ""
        while True:
            audio_chunk = audio_queue.get()
            audio_chunk = audio_chunk.flatten().astype(np.float32)
            result = model.transcribe(audio_chunk, language="en", word_timestamps=True)
            speech_text = result["text"].strip()
            # Check for no_speech_prob in the first segment
            if "segments" in result and result["segments"]:
                no_speech_prob = result["segments"][0].get("no_speech_prob", 0)
                if no_speech_prob > 0.5:
                    continue  # Skip if likely no speech
            if "bono" in speech_text.lower():
                print("Chef Bono detected in speech!\n")
                speech_text = ""
                listen_for_bono(stop_word="chef")

    except Exception as e:
        print(f"Error in processing thread: {e}")
        stop_recording.set()  # Signal main thread to stop on error
    finally:
        # Cleanup: clear the queue
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
                # phrase_time_limit keeps each capture short (prevents "forever recording")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=6)

                text = recognizer.recognize_google(audio)

                normalized = text.lower()

                # simplest match (substring)
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
    global audio_queue, stop_recording, response, processing_thread

    # Reset global state before starting a new session
    response = ""  # Clear previous response
    stop_recording.clear()
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

    # Give the processing thread a moment to finish
    processing_thread.join(timeout=1)

    return response


if __name__ == "__main__":
    stt_model = initialize_model()
    listen(stt_model)
