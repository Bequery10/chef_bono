import speech_recognition as sr
import time


def continuous_listening_forever():
    """
    Continuously listen and recognize speech until Ctrl+C.
    Uses Pocketsphinx (offline, no API calls).
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True

    with sr.Microphone() as source:
        print("🎤 Listening continuously... (Press Ctrl+C to stop)")
        print("-" * 50)

        try:
            while True:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    # Use Pocketsphinx instead of Google (offline)
                    text = recognizer.recognize_sphinx(audio)
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] ✅ {text}")

                except sr.UnknownValueError:
                    pass  # Silence, no match
                except sr.RequestError as e:
                    print(f"[ERROR] API error: {e}")
                except sr.exceptions.WaitTimeoutError:
                    pass  # No audio detected in timeout

        except KeyboardInterrupt:
            print("\n" + "-" * 50)
            print("⏹️ Stopped listening")


if __name__ == "__main__":
    continuous_listening_forever()
