import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import os
import subprocess
from vosk import Model, KaldiRecognizer


os.environ["FLAC_EXECUTABLE"] = "/opt/homebrew/bin/flac"


def record_audio(filename="output.wav", duration=5, fs=44100):
    print(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()  # Wait until recording is finished
    write(filename, fs, audio)
    print(f"Recording saved as {filename}")


def get_text(audio_file_path):
    # Path to your Vosk model directory
    model_path = "stt_model"  # Change if your model is in a different folder

    if not os.path.exists(model_path):
        print(
            f"Please download a Vosk model and unpack as '{model_path}' in the current folder."
        )
        return

    model = Model(model_path)
    rec = KaldiRecognizer(model, 44100)

    import wave

    with wave.open(audio_file_path, "rb") as wf:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                pass
        result = rec.FinalResult()
        import json

        text = str(json.loads(result).get("text", ""))

        print("Transcription:", text)
        if text.strip().lower() == "start":
            print("Activation word detected.")


if __name__ == "__main__":
    audio_path = "output.wav"
    record_audio(audio_path, duration=3)
    get_text(audio_path)
