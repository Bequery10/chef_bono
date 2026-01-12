import pyttsx3


def play_sound(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    play_sound("Hello, this is chef bono!")
