from tts_and_stt.stt1 import listen, start_flask_app
import warnings
import time
import os

warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")
if __name__ == "__main__":
    flask_proc = start_flask_app()

    try:
        while True:
            speech = listen()
            print(f"You said: {speech}")
    except KeyboardInterrupt:
        flask_proc.terminate()
        os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
