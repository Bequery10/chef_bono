import io
import wave
import tempfile
import subprocess
import os
import threading
import base64
import requests
from piper.voice import PiperVoice
from tts_and_stt.flags import bono_started_speaking, bono_stopped_speaking

# Track the current playback process
_current_playback_process = None
_playback_lock = threading.Lock()

WEB_API_BASE = "http://127.0.0.1:5001"


def play(text: str, model_path: str = None):
    """
    Synthesize text and play it in the background (non-blocking).
    Sends WAV data to web_api_app.py for browser distribution.
    """
    if model_path is None:
        model_path = "/Users/berkan/Desktop/Projects/chef_bono/tts_and_stt/tts_models/en_US-hfc_female-medium/en_US-hfc_female-medium.onnx"

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    voice = PiperVoice.load(model_path)

    # Synthesize to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
        with wave.open(tmp_path, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)

    # Read the WAV file as bytes
    with open(tmp_path, "rb") as f:
        wav_bytes = f.read()

    # Send to web_api_app.py for distribution to browser
    try:
        wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")
        requests.post(
            f"{WEB_API_BASE}/control/tts_waveform",
            json={"wav_data": wav_b64, "text": text},
            timeout=2,
        )
    except Exception as e:
        print(f"[WARNING] Failed to send TTS waveform to browser: {e}")

    # Run audio playback in a background thread
    def play_audio():
        global _current_playback_process

        try:
            if "bono" in text.lower():
                bono_started_speaking("1")
            else:
                bono_started_speaking("-1")

            with _playback_lock:
                _current_playback_process = subprocess.Popen(
                    ["afplay", tmp_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            _current_playback_process.wait()
        except Exception as e:
            print(f"[ERROR] Playback failed: {e}")
        finally:
            with _playback_lock:
                _current_playback_process = None
            os.unlink(tmp_path)
            bono_stopped_speaking()

    thread = threading.Thread(target=play_audio, daemon=True)
    thread.start()


def stop_bono_speaking():
    """Stop the currently playing audio immediately."""
    global _current_playback_process

    with _playback_lock:
        if _current_playback_process is not None:
            try:
                _current_playback_process.terminate()
                _current_playback_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                _current_playback_process.kill()
            _current_playback_process = None
