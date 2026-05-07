import subprocess
import time
import os
import platform
import warnings
from tts_and_stt.web_api_app import (
    get_latest_transcript,
    start_listening_browser,
    stop_listening_browser,
)

warnings.filterwarnings("ignore")


def get_speech():
    speech = ""
    start_time = time.time()
    stop_listening = False
    print(f"Latest transcript: {speech}")
    while not stop_listening:
        if speech:
            start_time = time.time()
            speech = get_latest_transcript()

        elif time.time() - start_time > 5:
            stop_to_listen()

    return speech


def is_bono_said():
    command = get_latest_transcript()
    print(f"bono ?: {command}")
    return "bono" in command.lower()


def listen():
    start_listening_browser()

    while not is_bono_said():
        time.sleep(0.1)

    return get_speech()


def stop_to_listen():
    stop_listening_browser()


def start_flask_app():
    os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
    time.sleep(1)
    os.system("clear")

    flask_process = subprocess.Popen(
        ["python", "web_api_app.py"],
        cwd="tts_and_stt",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    time.sleep(5)

    if platform.system() == "Darwin":
        subprocess.Popen(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--user-data-dir=/tmp/chrome_temp_bono",
                "--disable-sync",
                "--no-first-run",
                "http://127.0.0.1:5001",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    print("Listening for 'bono'...")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        flask_process.terminate()
        os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
