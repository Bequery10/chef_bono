import subprocess
import time
import os
import platform
import warnings
from tts_and_stt.web_api_app import (
    get_latest_transcript,
    start_listening_browser,
    stop_listening_browser,
    is_browser_connected,
)

warnings.filterwarnings("ignore")


def get_speech():
    speech = ""
    start_time = time.time()
    stop_listening = False
    while not stop_listening:
        time.sleep(0.1)
        latest_speech = get_latest_transcript()
        speech += latest_speech
        if latest_speech:
            start_time = time.time()

        elif time.time() - start_time > 5:
            stop_listening = True
            stop_to_listen()

    return speech


def is_bono_said():
    command = get_latest_transcript()
    return "bono" in command.lower()


def wait_for_browser_connection(timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        if is_browser_connected():
            return True
        time.sleep(0.1)
    return False


def listen():
    if not wait_for_browser_connection():
        raise Exception("Browser failed to connect")

    start_listening_browser()
    while not is_bono_said():
        time.sleep(0.1)

    return get_speech()


def stop_to_listen():
    stop_listening_browser()


def start_flask_app():
    os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
    time.sleep(1)

    flask_process = subprocess.Popen(
        ["python", "web_api_app.py"],
        cwd="tts_and_stt",
        # Don't pipe - let output go to terminal
        text=True,
    )

    time.sleep(5)

    if platform.system() == "Darwin":
        subprocess.Popen(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--user-data-dir=/tmp/chrome_temp_bono",
                "--disable-sync",
                "--no-first-run",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "http://127.0.0.1:5001",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    return flask_process
