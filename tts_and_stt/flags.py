import os

BONO_SPEAKING_FLAG = "/tmp/bono_speaking"


def bono_started_speaking():
    with open(BONO_SPEAKING_FLAG, "w") as f:
        f.write("1")


def bono_stopped_speaking():
    if os.path.exists(BONO_SPEAKING_FLAG):
        os.remove(BONO_SPEAKING_FLAG)


def is_bono_speaking():
    return os.path.exists(BONO_SPEAKING_FLAG)
