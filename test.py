from tts_and_stt.stt1 import listen, start_flask_app
import warnings

warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")
if __name__ == "__main__":
    start_flask_app()
    while True:
        speech = listen()
        print(f"You said: {speech}")
