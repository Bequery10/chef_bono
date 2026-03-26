import edge_tts
import asyncio


async def text_to_speech(text):
    print("Ses oluşturuluyor...")
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural")
    await communicate.save("output.mp3")
    print("Ses dosyası oluşturuldu: output.mp3")


def main():
    text = "Merhaba, ben chef bono!"
    asyncio.run(text_to_speech(text))


if __name__ == "__main__":
    main()
