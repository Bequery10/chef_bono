import os

BONO_SPEAKING_FLAG = "/tmp/bono_speaking"
USER_SPEAKING_FLAG = "/tmp/user_speaking"


def bono_started_speaking(data):
    with open(BONO_SPEAKING_FLAG, "w") as f:
        f.write(data)


def bono_stopped_speaking():
    if os.path.exists(BONO_SPEAKING_FLAG):
        os.remove(BONO_SPEAKING_FLAG)


def is_bono_speaking():
    if os.path.exists(BONO_SPEAKING_FLAG):
        with open(BONO_SPEAKING_FLAG, "r") as f:
            data = f.read().strip()
            return data
    return False


def user_started_speaking():
    with open(USER_SPEAKING_FLAG, "w") as f:
        f.write("1")


def user_stopped_speaking():
    if os.path.exists(USER_SPEAKING_FLAG):
        os.remove(USER_SPEAKING_FLAG)


def is_user_speaking():
    return os.path.exists(USER_SPEAKING_FLAG)
