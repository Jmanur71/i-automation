import sounddevice as sd
import numpy as np
from config import SAMPLE_RATE, LOGGER

class WakeWordDetector:
    def __init__(self, wake_word="hey parakeet"):
        self.wake_word = wake_word.lower()
        self.is_listening = False
        
    def listen_for_wake_word(self, callback):
        """Continuously listen for wake word"""
        self.is_listening = True
        LOGGER.info(f'Wake word detector started. Say "{self.wake_word}"')
        
        while self.is_listening:
            try:
                # Record 3 seconds at a time
                audio = sd.rec(int(SAMPLE_RATE * 3), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
                sd.wait()
                
                # Check if audio contains wake word (simple energy detection)
                audio = np.squeeze(audio)
                energy = np.abs(audio).mean()
                
                if energy > 100:  # Speech detected
                    LOGGER.debug('Speech detected, checking for wake word')
                    callback()  # Trigger recording
                    
            except Exception as e:
                LOGGER.error(f'Wake word detection error: {e}')
                
    def stop(self):
        self.is_listening = False
