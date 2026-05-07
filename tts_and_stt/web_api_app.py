from flask import Flask
from flask_socketio import SocketIO, emit
import os
import warnings

warnings.filterwarnings("ignore")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

detected_bono = False
last_transcript = ""


@app.route("/")
def index():
    html_file = os.path.join(os.path.dirname(__file__), "web_api.html")
    with open(html_file, "r") as f:
        return f.read()


@socketio.on("transcript")
def handle_transcript(data):
    global detected_bono, last_transcript
    transcript = data.get("text", "").lower()
    last_transcript = transcript


@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("disconnect")
def handle_disconnect():
    pass


def get_latest_transcript():
    global last_transcript
    return last_transcript


def start_listening_browser():
    """Tell browser to start listening"""
    socketio.emit("start_listening")


def stop_listening_browser():
    """Tell browser to stop listening"""
    socketio.emit("stop_listening")


if __name__ == "__main__":
    socketio.run(app, debug=False, host="0.0.0.0", port=5001)
