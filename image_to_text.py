from ai_utils import AIUtils

if __name__ == "__main__":
    ai = AIUtils()
    result = ai.image_to_text()
    with open("questions.txt", "w") as f:
        f.write(result)
