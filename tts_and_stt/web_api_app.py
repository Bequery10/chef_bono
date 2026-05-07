from flask import Flask
from flask_socketio import SocketIO, emit
import os
import warnings
import fcntl

warnings.filterwarnings("ignore")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

detected_bono = False
CONNECTED_FLAG_FILE = "/tmp/bono_browser_connected"
TRANSCRIPT_FILE = "/tmp/bono_latest_transcript"  # Store transcript in a file


@app.route("/")
def index():
    html_file = os.path.join(os.path.dirname(__file__), "web_api.html")
    with open(html_file, "r") as f:
        return f.read()


@socketio.on("transcript")
def handle_transcript(data):
    global detected_bono
    transcript = data.get("text", "").lower()
    # Write to file so main process can read it
    try:
        with open(TRANSCRIPT_FILE, "a") as f:  # "a" append mode
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
            f.write(transcript + "\n")  # Append with newline
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
    except Exception as e:
        pass


@socketio.on("connect")
def handle_connect():
    with open(CONNECTED_FLAG_FILE, "w") as f:
        f.write("1")


@socketio.on("disconnect")
def handle_disconnect():
    if os.path.exists(CONNECTED_FLAG_FILE):
        os.remove(CONNECTED_FLAG_FILE)


def get_latest_transcript():
    if os.path.exists(TRANSCRIPT_FILE):
        try:
            with open(TRANSCRIPT_FILE, "r+") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
                transcript = f.read()
                f.seek(0)
                f.truncate()  # Clear file atomically
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
                return transcript
        except Exception as e:
            print(f"Error reading transcript: {e}")
            return ""
    return ""


def is_browser_connected():
    return os.path.exists(CONNECTED_FLAG_FILE)


def start_listening_browser():
    socketio.emit("start_listening")


def stop_listening_browser():
    socketio.emit("stop_listening")


if __name__ == "__main__":
    socketio.run(app, debug=False, host="0.0.0.0", port=5001)
