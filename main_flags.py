IS_PROMPTING_AVAILABLE = "/tmp/is_prompting_available"


def set_prompting_available():
    with open(IS_PROMPTING_AVAILABLE, "w") as f:
        f.write("1")


def is_prompting_available():
    try:
        with open(IS_PROMPTING_AVAILABLE, "r") as f:
            return f.read() == "1"
    except FileNotFoundError:
        return False


def set_prompting_unavailable():
    if os.path.exists(IS_PROMPTING_AVAILABLE):
        os.remove(IS_PROMPTING_AVAILABLE)
