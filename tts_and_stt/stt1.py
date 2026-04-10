import os

# Ensure Homebrew binaries (like `flac`) are found first
brew_bin = "/opt/homebrew/bin"
current_path = os.environ.get("PATH", "")
if not current_path.startswith(brew_bin + ":"):
    os.environ["PATH"] = f"{brew_bin}:{current_path}"

import speech_recognition as sr


def callback(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")


def main():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    print("Listening in the background... (Ctrl+C to exit)")
    stop_listening = recognizer.listen_in_background(mic, callback)
    try:
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        stop_listening(wait_for_stop=False)
        print("Stopped.")


if __name__ == "__main__":
    main()
