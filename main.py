import os
import re
import ai_utils


if __name__ == "__main__":

    Exit = False
    model = ai_utils.AIUtils("gemini-2.0-flash")

    model._analyze_kitchen_image("general")
