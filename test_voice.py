import sounddevice as sd
from scipy.io.wavfile import write
import whisper
import edge_tts
import asyncio
import soundfile as sf
import numpy as np


def record_audio(filename="input.wav", duration=5, fs=16000):
    print("Konuş...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write(filename, fs, recording)
    print("Kayıt tamam.")


def speech_to_text(filename="input.wav"):
    print("Model yükleniyor...")
    model = whisper.load_model("base")

    print("Ses çözümleniyor...")
    audio, sr = sf.read(filename, dtype="float32")

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    audio = audio.astype(np.float32)

    result = model.transcribe(audio, language="tr")
    text = result["text"]

    # Text dosyasına kaydet
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Text dosyası oluşturuldu: output.txt")

    print("Algılanan:", text)
    return text


async def text_to_speech(text):
    print("Ses oluşturuluyor...")
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural")
    await communicate.save("output.mp3")
    print("Ses dosyası oluşturuldu: output.mp3")


def main():
    record_audio()
    text = speech_to_text()

    if text.strip() == "":
        text = "Seni anlayamadım"

    asyncio.run(text_to_speech(text))


if __name__ == "__main__":
    main()
    print("Test tamamlandı.")
