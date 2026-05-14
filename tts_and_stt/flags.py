import os

BONO_SPEAKING_FLAG = "/tmp/bono_speaking"
USER_SPEAKING_FLAG = "/tmp/user_speaking"
APP_STARTED_FLAG = "/tmp/app_started"
APP_CONVO_ALIVE_FLAG = "/tmp/app_convo_alive"


def is_convo_alive():
    return os.path.exists(APP_CONVO_ALIVE_FLAG)


def set_convo_alive():
    with open(APP_CONVO_ALIVE_FLAG, "w") as f:
        f.write("1")


def clear_convo_alive():
    if os.path.exists(APP_CONVO_ALIVE_FLAG):
        os.remove(APP_CONVO_ALIVE_FLAG)


def has_app_started():
    return os.path.exists(APP_STARTED_FLAG)


def set_app_started():
    with open(APP_STARTED_FLAG, "w") as f:
        f.write("1")


def clear_app_started():
    if os.path.exists(APP_STARTED_FLAG):
        os.remove(APP_STARTED_FLAG)


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
