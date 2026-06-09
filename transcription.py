import speech_recognition as sr
import threading
import numpy as np
import tempfile
import wave
import os
from config import SAMPLE_RATE, LOGGER, RECOGNITION_LANGUAGE, NORMALIZE_AUDIO, WHISPER_ENABLED, WHISPER_BACKEND, WHISPER_MODEL

# Try importing optional Whisper backends lazily
_HAS_FASTER_WHISPER = False
_HAS_WHISPER = False
try:
    if WHISPER_ENABLED:
        from faster_whisper import WhisperModel
        _HAS_FASTER_WHISPER = True
except Exception:
    _HAS_FASTER_WHISPER = False

try:
    if WHISPER_ENABLED and not _HAS_FASTER_WHISPER:
        import whisper as _whisper
        _HAS_WHISPER = True
except Exception:
    _HAS_WHISPER = False

class TranscriptionEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.lock = threading.Lock()
        self._whisper_model = None
        
    def transcribe(self, audio_data):
        if not audio_data:
            LOGGER.debug('No audio data provided for transcription')
            return ""

        if NORMALIZE_AUDIO:
            audio_data = self._normalize(audio_data)

        # If Whisper is enabled and available, use it (prefer faster_whisper)
        if WHISPER_ENABLED and (_HAS_FASTER_WHISPER or _HAS_WHISPER):
            try:
                text = self._transcribe_with_whisper(audio_data)
                if text:
                    LOGGER.info(f'Whisper transcription successful: "{text}"')
                    return text.strip()
            except Exception as e:
                LOGGER.exception('Whisper transcription failed, falling back to Google: %s', e)

        # Fallback to Google SpeechRecognition
        try:
            with self.lock:
                audio = sr.AudioData(audio_data, SAMPLE_RATE, 2)
                # Adjust recognizer for better accuracy
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                
                text = self.recognizer.recognize_google(audio, language=RECOGNITION_LANGUAGE, show_all=False)
                LOGGER.info(f'Transcription successful: "{text}"')
                return text.strip()
        except sr.UnknownValueError:
            LOGGER.warning('Speech not recognized (inaudible audio)')
            return ""
        except sr.RequestError as e:
            LOGGER.error(f'Transcription API error: {e}')
            return ""

    def _transcribe_with_whisper(self, audio_data: bytes) -> str:
        # write to a temporary WAV file
        tf = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        try:
            with wave.open(tf.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data)

            if _HAS_FASTER_WHISPER:
                if self._whisper_model is None:
                    LOGGER.info('Loading faster-whisper model: %s', WHISPER_MODEL)
                    self._whisper_model = WhisperModel(WHISPER_MODEL, device='cpu', compute_type='int8')
                segments, info = self._whisper_model.transcribe(tf.name, beam_size=5, language=RECOGNITION_LANGUAGE)
                text = ' '.join([s.text for s in segments]).strip()
                return text

            if _HAS_WHISPER:
                if self._whisper_model is None:
                    LOGGER.info('Loading openai-whisper model: %s', WHISPER_MODEL)
                    self._whisper_model = _whisper.load_model(WHISPER_MODEL)
                result = self._whisper_model.transcribe(tf.name, language=RECOGNITION_LANGUAGE)
                return result.get('text', '').strip()

            return ''
        finally:
            try:
                tf.close()
            except Exception:
                pass
            try:
                os.remove(tf.name)
            except Exception:
                pass

    def _normalize(self, audio_data):
        audio = np.frombuffer(audio_data, dtype=np.int16)
        peak = np.max(np.abs(audio))
        if peak == 0 or peak > 12000:
            return audio_data
        factor = 12000.0 / peak
        normalized = np.clip((audio.astype(np.float32) * factor), -32768, 32767).astype(np.int16)
        return normalized.tobytes()
