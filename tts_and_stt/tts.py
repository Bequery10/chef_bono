import io
import wave
import tempfile
import subprocess
import os
from piper.voice import PiperVoice


def play(text: str, model_path: str = None):
    """
    Synthesize







     text and play it directly to speakers.

    Args:
        text: Text to speak
        model_path: Path to .onnx model file
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

    try:
        # Play with macOS afplay (or substitute your OS's player)
        subprocess.run(["afplay", tmp_path], check=True)
    finally:
        os.unlink(tmp_path)
