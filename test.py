from tts_and_stt import tts
from tts_and_stt import stt
import warnings

stt_model = stt.initialize_model()
warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")
if __name__ == "__main__":
    while True:
        recorded_audio = stt.listen(model=stt_model)
        print(f"recorded_audio: {recorded_audio}")
        tts.play(f"hey")
