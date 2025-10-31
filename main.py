import os
import re
import ai_utils


if __name__ == "__main__":

    Exit = False
    chat = ai_utils.AIUtils("gemini-2.0-flash")

    while not Exit:
        instruction = stt.get_text()
        response = chat.ask_ai(instruction)
        tts.play_sound(response)
        # WRONG STRUCTURE
