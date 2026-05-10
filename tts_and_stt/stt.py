import subprocess
import time
import os
import platform
import warnings
from tts_and_stt.web_api_app import (
    get_latest_transcript,
    is_browser_connected,
    clear_transcript_file,
)
from tts_and_stt.tts import play
from tts_and_stt.flags import is_bono_speaking

warnings.filterwarnings("ignore")


# Debug flag - set to False to disable debug messages
DEBUG = False

import requests

WEB_API_BASE = "http://127.0.0.1:5001"


def start_listening_browser_remote():
    requests.post(f"{WEB_API_BASE}/control/start_listening", timeout=2)


def stop_listening_browser_remote():
    requests.post(f"{WEB_API_BASE}/control/stop_listening", timeout=2)


def get_speech():
    if DEBUG:
        print(f"[DEBUG] get_speech() started")
    speech = ""
    start_time = time.time()
    stop_listening = False
    while not stop_listening:
        time.sleep(0.1)
        latest_speech = get_latest_transcript()
        if latest_speech:
            if DEBUG:
                print(f"[DEBUG] Received speech segment: '{latest_speech}'")

        if speech == "" and latest_speech.startswith("yes"):
            if DEBUG:
                print(f"[DEBUG] Removing 'yes' prefix from first segment")
            latest_speech = latest_speech[3:].strip()
            if DEBUG:
                print(f"[DEBUG] After removing 'yes': '{latest_speech}'")

        if latest_speech:
            if DEBUG:
                print(f"[DEBUG] Appending to speech buffer")
            speech += latest_speech
            if DEBUG:
                print(f"[DEBUG] Current speech buffer: '{speech}'")
            start_time = time.time()
            if DEBUG:
                print(f"[DEBUG] Reset timeout timer")
        else:
            elapsed = time.time() - start_time
            if elapsed > 3:
                if DEBUG:
                    print(
                        f"[DEBUG] Timeout reached ({elapsed:.1f}s > 3s). Stopping listening."
                    )
                stop_listening = True
                stop_to_listen()

    if DEBUG:
        print(f"[DEBUG] get_speech() completed. Final speech: '{speech}'")
    return speech


def is_bono_said():
    if DEBUG:
        print(f"[DEBUG] Checking if 'bono' was mentioned...")
    command = get_latest_transcript()
    result = "bono" in command.lower()
    if DEBUG:
        print(f"[DEBUG] Transcript check: '{command}' | Contains 'bono': {result}")
    return result


def wait_for_browser_connection(timeout=20):
    if DEBUG:
        print(f"[DEBUG] Waiting for browser connection (timeout: {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        if is_browser_connected():
            if DEBUG:
                print(f"[DEBUG] Browser connected!")
            return True
        time.sleep(0.05)
    if DEBUG:
        print(f"[DEBUG] Browser connection timeout after {timeout}s")
    return False


def listen(greeting=False):
    if DEBUG:
        print(f"[DEBUG] listen() called with greeting={greeting}")

    if not wait_for_browser_connection():
        print(f"[ERROR] Browser connection failed")
        raise Exception("Browser failed to connect")

    if DEBUG:
        print(f"[DEBUG] Browser connected, proceeding...")

    if greeting:
        if DEBUG:
            print(f"[DEBUG] Playing greeting message")
        play("Welcome, I am chef Bono !")
        if DEBUG:
            print(f"[DEBUG] Greeting played")

    if DEBUG:
        print(f"[DEBUG] Clearing transcript file")
    clear_transcript_file()

    if DEBUG:
        print(f"[DEBUG] Waiting for Bono to finish speaking...")

    while is_bono_speaking():
        time.sleep(0.01)
    clear_transcript_file()
    if DEBUG:
        print(f"[DEBUG] Bono finished speaking")
    if DEBUG:
        print(f"[DEBUG] Starting browser listening...")
    start_listening_browser_remote()
    if DEBUG:
        print(f"[DEBUG] Waiting for user to say 'bono'...")
    while not is_bono_said():
        time.sleep(0.5)
    if DEBUG:
        print(f"[DEBUG] User said 'bono'! Playing confirmation...")
    play("Yes!")

    if DEBUG:
        print(f"[DEBUG] Now capturing full speech...")
    speech = get_speech()
    if DEBUG:
        print(f"[DEBUG] listen() completed with speech: '{speech}'")
    return speech


def stop_to_listen():
    if DEBUG:
        print(f"[DEBUG] Stopping browser listening...")
    stop_listening_browser_remote()
    if DEBUG:
        print(f"[DEBUG] Browser listening stopped")


def start_flask_app():
    if DEBUG:
        print("[DEBUG] Starting Flask app and browser setup...")
    os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
    if DEBUG:
        print("[DEBUG] Cleaned up existing port 5001")

    # Kill any existing Chrome processes
    os.system("pkill -f 'Google Chrome' 2>/dev/null || true")
    if DEBUG:
        print("[DEBUG] Cleaned up existing Chrome processes")

    time.sleep(1)

    if DEBUG:
        print("[DEBUG] Spawning Flask process...")
    flask_process = subprocess.Popen(
        ["python", "web_api_app.py"],
        cwd="tts_and_stt",
        text=True,
    )
    if DEBUG:
        print(f"[DEBUG] Flask process started (PID: {flask_process.pid})")

    time.sleep(5)
    if DEBUG:
        print("[DEBUG] Flask startup delay complete")

    if platform.system() == "Darwin":
        if DEBUG:
            print("[DEBUG] macOS detected. Launching Chrome headless...")
        subprocess.Popen(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--user-data-dir=/tmp/chrome_temp_bono",
                "--disable-sync",
                "--no-first-run",
                "--headless=new",
                "http://127.0.0.1:5001",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if DEBUG:
            print("[DEBUG] Chrome launched")

    if DEBUG:
        print("[DEBUG] Flask app and browser initialization complete")
    return flask_process
