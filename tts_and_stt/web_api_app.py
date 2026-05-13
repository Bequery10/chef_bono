from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, send

import os
import warnings
import fcntl
import logging
from tts_and_stt.flags import (
    bono_started_speaking,
    bono_stopped_speaking,
    user_started_speaking,
    user_stopped_speaking,
)

warnings.filterwarnings("ignore")

# Suppress Flask/Werkzeug request logs
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

# Suppress SocketIO logs
socketio_logger = logging.getLogger("socketio")
socketio_logger.setLevel(logging.ERROR)
engineio_logger = logging.getLogger("engineio")
engineio_logger.setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


# Debug flag - set to False to disable debug messages
DEBUG = False

# Tracks the most recently requested TTS playback.
_CURRENT_TTS_ID = None

CONNECTED_FLAG_FILE = "/tmp/bono_browser_connected"
TRANSCRIPT_FILE = "/tmp/bono_latest_transcript"  # Store transcript in a file


@app.route("/control/start_listening", methods=["POST"])
def control_start_listening():
    if not is_browser_connected():
        return jsonify({"ok": False, "error": "browser_not_connected"}), 409
    start_listening_browser()
    return jsonify({"ok": True}), 200


@app.route("/control/stop_listening", methods=["POST"])
def control_stop_listening():
    if not is_browser_connected():
        return jsonify({"ok": False, "error": "browser_not_connected"}), 409
    stop_listening_browser()
    return jsonify({"ok": True}), 200


@app.route("/control/stop_tts", methods=["POST"])
def control_stop_tts():
    """Stop any in-browser TTS playback."""
    global _CURRENT_TTS_ID
    _CURRENT_TTS_ID = None
    try:
        bono_stopped_speaking()
    except Exception:
        pass

    socketio.emit("stop_tts")
    return jsonify({"ok": True}), 200


def _emit_set_language(language):
    """Helper function to emit language change to connected clients."""
    if language.lower() == "english":
        language = "en-US"
    elif language.lower() == "turkish":
        language = "tr-TR"

    socketio.emit("set_language", {"language": language})
    if DEBUG:
        print(f"[DEBUG] Language set to: {language}")
    return language


@app.route("/control/set_language", methods=["POST"])
def set_language():
    language = request.args.get("language", "english")
    result_lang = _emit_set_language(language)
    return jsonify({"ok": True, "language": result_lang}), 200


@app.route("/")
def index():
    html_file = os.path.join(os.path.dirname(__file__), "web_api.html")
    with open(html_file, "r") as f:
        return f.read()


@socketio.on("transcript")
def handle_transcript(data):
    transcript = data.get("text", "").lower()
    if DEBUG:
        print(
            f"Received transcript from browser: '{transcript}' now will be written to file"
        )

    # Write to file so main process can read it
    try:
        with open(TRANSCRIPT_FILE, "a") as f:  # "a" append mode

            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock

            f.write(transcript + "\n")  # Append with newline

            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock

    except Exception as e:
        print(f"[ERROR] Failed to write transcript: {e}")


@socketio.on("user_started_speaking")
def handle_user_speaking():
    user_started_speaking()


@socketio.on("user_stopped_speaking")
def handle_user_stopped_speaking():
    user_stopped_speaking()


@socketio.on("connect")
def handle_connect():
    if DEBUG:
        print("[DEBUG] 🔗 Browser connected to SocketIO")
    with open(CONNECTED_FLAG_FILE, "w") as f:
        f.write("1")
    if DEBUG:
        print("[DEBUG] Connection flag file created")


@socketio.on("disconnect")
def handle_disconnect():
    if DEBUG:
        print("[DEBUG] 🔌 Browser disconnected from SocketIO")
    if os.path.exists(CONNECTED_FLAG_FILE):
        os.remove(CONNECTED_FLAG_FILE)
        if DEBUG:
            print("[DEBUG] Connection flag file removed")


@socketio.on("log_error")
def handle_log_error(data):
    error_msg = data.get("error")
    print(f"🔴 [DEBUG] Browser Error Event: {error_msg}")


@socketio.on("log_info")
def handle_log_info(data):
    info_msg = data.get("message")
    print(f"ℹ️ [DEBUG] Browser Info Event: {info_msg}")


@socketio.on("tts_playback_ended")
def handle_tts_playback_ended(data):
    """Browser notifies that a TTS buffer finished playing."""
    global _CURRENT_TTS_ID

    data = data or {}
    ended_id = data.get("tts_id")

    # Ignore stale ended events when a newer TTS has already started.
    if ended_id and _CURRENT_TTS_ID and ended_id != _CURRENT_TTS_ID:
        if DEBUG:
            print(
                f"[DEBUG] Ignoring stale tts_playback_ended: {ended_id} (current: {_CURRENT_TTS_ID})"
            )
        return

    _CURRENT_TTS_ID = None
    try:
        bono_stopped_speaking()
    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] Failed to clear speaking flag: {e}")


def clear_transcript_file():
    """Clear the transcript file to start fresh"""
    if DEBUG:
        print(f"[DEBUG] Clearing transcript file: {TRANSCRIPT_FILE}")
    if os.path.exists(TRANSCRIPT_FILE):
        try:
            with open(TRANSCRIPT_FILE, "w") as f:

                fcntl.flock(f.fileno(), fcntl.LOCK_EX)

                f.truncate()

                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            print(f"[ERROR] Error clearing transcript: {e}")
    else:
        if DEBUG:
            print(f"[DEBUG] Transcript file doesn't exist yet: {TRANSCRIPT_FILE}")


def get_latest_transcript():
    if os.path.exists(TRANSCRIPT_FILE):
        try:
            if DEBUG:
                print(f"[DEBUG] Reading from transcript file: {TRANSCRIPT_FILE}")
            with open(TRANSCRIPT_FILE, "r+") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
                transcript = f.read()
                f.seek(0)
                f.truncate()  # Clear file atomically
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
            return transcript
        except Exception as e:
            print(f"[ERROR] Error reading transcript: {e}")
            return ""
    else:
        if DEBUG:
            print(f"[DEBUG] Transcript file does not exist yet: {TRANSCRIPT_FILE}")
    return ""


def is_browser_connected():
    result = os.path.exists(CONNECTED_FLAG_FILE)
    if DEBUG:
        print(f"[DEBUG] Browser connection check: {result}")
    return result


def start_listening_browser():
    if DEBUG:
        print(f"[DEBUG] Emitting 'start_listening' signal to browser...")
    socketio.emit("start_listening")  # Pass empty dict as data
    if DEBUG:
        print(f"[DEBUG] 'start_listening' signal emitted")


def stop_listening_browser():
    if DEBUG:
        print("[DEBUG] Emitting stop_listening to browser...")
    socketio.emit("stop_listening")  # Pass empty dict as data
    if DEBUG:
        print("[DEBUG] 'stop_listening' signal emitted")


if __name__ == "__main__":
    socketio.run(app, debug=False, host="0.0.0.0", port=5001)
