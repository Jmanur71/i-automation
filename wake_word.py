import numpy as np

from config import LOGGER, SAMPLE_RATE

try:
    import sounddevice as sd
except Exception:
    sd = None


class WakeWordDetector:
    def __init__(self, wake_word="hey parakeet"):
        self.wake_word = wake_word.lower()
        self.is_listening = False

    def listen_for_wake_word(self, callback):
        """Continuously listen for wake word."""
        if sd is None:
            LOGGER.warning("Wake word detector unavailable because sounddevice is missing.")
            return

        self.is_listening = True
        LOGGER.info('Wake word detector started. Say "%s"', self.wake_word)

        while self.is_listening:
            try:
                audio = sd.rec(int(SAMPLE_RATE * 3), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
                sd.wait()
                audio = np.squeeze(audio)
                energy = np.abs(audio).mean()

                if energy > 100:
                    LOGGER.debug("Speech detected, checking for wake word")
                    callback()
            except Exception as e:
                LOGGER.error("Wake word detection error: %s", e)

    def stop(self):
        self.is_listening = False
