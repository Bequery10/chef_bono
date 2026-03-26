import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import soundfile as sf
import numpy as np


def record_audio(filename="input.wav", duration=5, fs=16000):
    print("Speak...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, recording)
    print("Recording completed.")


def speech_to_text(filename="input.wav"):
    print("Model is loading...")
    model = whisper.load_model("base")

    print("Speech is being transcribed...")
    audio, sr = sf.read(filename, dtype="float32")

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    audio = audio.astype(np.float32)

    result = model.transcribe(audio, language="tr")
    text = result["text"]

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("created text file: output.txt")

    print("Heard:", text)
    return text


def main():
    record_audio()
    text = speech_to_text()

    if text.strip() == "":
        text = "Seni anlayamadım"


if __name__ == "__main__":
    main()
    print("Finished processing.")
