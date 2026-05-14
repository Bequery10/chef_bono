import subprocess
import time
import os
import platform
import warnings
from tts_and_stt.web_api_app import (
    get_latest_transcript,
    is_browser_connected,
    clear_transcript_file,
    _emit_set_language,
)
from tts_and_stt.tts import play, stop_bono_speaking
from tts_and_stt.flags import (
    is_bono_speaking,
    is_user_speaking,
    has_app_started,
    clear_app_started,
)

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
            speech += latest_speech
            start_time = time.time()
        else:
            elapsed = time.time() - start_time
            if elapsed > 3:
                stop_listening = True
                stop_to_listen()

    return speech


def is_bono_said():

    command = get_latest_transcript()
    # print("commdand: ", command)
    result = "bono" in command.lower()
    if result:
        print("bono was said!")
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


def listen(greeting=False, language="english"):
    print("listen() called, waiting for browser connection...")

    if not wait_for_browser_connection():
        print(f"[ERROR] Browser connection failed")
        raise Exception("Browser failed to connect")

    while not has_app_started():
        time.sleep(0.1)
        # print("Waiting for app to signal it has started...")

    if greeting:
        _emit_set_language(language)
        if language.lower() == "english":
            play("Welcome, I am chef Bono !", language=language)
        elif language.lower() == "turkish":
            play("Hoş geldin, ben şef Bono!", language=language)

        while is_bono_speaking():
            time.sleep(0.1)

    start_listening_browser_remote()
    print("Waiting for user to say 'bono'...")
    bono_not_said = not is_bono_said()
    sentence_has_no_bono = not (is_bono_speaking() and is_bono_speaking() == "1")
    while bono_not_said and sentence_has_no_bono:

        bono_not_said = not is_bono_said()
        sentence_has_no_bono = not (is_bono_speaking() and is_bono_speaking() == "1")

        time.sleep(0.05)
        # print("loop")

    print("Bono was said, starting to listen for user speech...")
    stop_bono_speaking()

    if language.lower() == "english":
        play("Yes?", language=language)
    elif language.lower() == "turkish":
        play("Evet?", language=language)

    while is_user_speaking():
        time.sleep(0.1)

    stop_listening_browser_remote()

    speech = get_latest_transcript()
    if speech.startswith("yes"):
        speech = speech[3:].strip()

    return speech


def stop_to_listen():
    if DEBUG:
        print(f"[DEBUG] Stopping browser listening...")
    stop_listening_browser_remote()
    if DEBUG:
        print(f"[DEBUG] Browser listening stopped")


def start_flask_app(language="english"):
    if DEBUG:
        print("[DEBUG] Starting Flask app and browser setup...")
    os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
    if DEBUG:
        print("[DEBUG] Cleaned up existing port 5001")

    clear_app_started()

    # Kill any existing Chrome processes
    os.system("pkill -f 'Google Chrome' 2>/dev/null || true")
    if DEBUG:
        print("[DEBUG] Cleaned up existing Chrome processes")

    time.sleep(1)

    if DEBUG:
        print("[DEBUG] Spawning Flask process...")
    child_env = os.environ.copy()
    child_env["BONO_PARENT_PID"] = str(os.getpid())

    flask_process = subprocess.Popen(
        ["python", "-m", "tts_and_stt.web_api_app"],
        cwd=".",
        text=True,
        env=child_env,
    )
    if DEBUG:
        print(f"[DEBUG] Flask process started (PID: {flask_process.pid})")

    time.sleep(5)
    if DEBUG:
        print("[DEBUG] Flask startup delay complete")

    browser_language = "en-US"  # Default to English

    if language.lower() == "turkish":
        browser_language = "tr-TR"

    if platform.system() == "Darwin":
        if DEBUG:
            print("[DEBUG] macOS detected. Launching Chrome headless...")
        subprocess.Popen(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "--user-data-dir=/tmp/chrome_temp_bono",
                "--disable-sync",
                "--no-first-run",
                # "--headless=new",
                f"http://127.0.0.1:5001/?lang={browser_language}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if DEBUG:
            print("[DEBUG] Chrome launched")

    if DEBUG:
        print("[DEBUG] Flask app and browser initialization complete")
    return flask_process
