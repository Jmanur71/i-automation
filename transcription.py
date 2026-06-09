import os
import tempfile
import threading
import wave

import numpy as np

from config import (
    LOGGER,
    NORMALIZE_AUDIO,
    RECOGNITION_LANGUAGE,
    SAMPLE_RATE,
    TRANSCRIPTION_CONFIDENCE_THRESHOLD,
    WHISPER_BACKEND,
    WHISPER_ENABLED,
    WHISPER_MODEL,
)

try:
    import speech_recognition as sr
except Exception:
    sr = None

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
        self.recognizer = sr.Recognizer() if sr else None
        self.lock = threading.Lock()
        self._whisper_model = None
        self._corrections = [
            ("stateful state", "stateful set"),
            ("c i c d", "ci/cd"),
            ("cicd", "ci/cd"),
            ("v p c", "vpc"),
        ]

    def transcribe(self, audio_data):
        if not audio_data:
            LOGGER.debug("No audio data provided for transcription")
            return ""

        if NORMALIZE_AUDIO:
            audio_data = self._normalize(audio_data)

        if WHISPER_ENABLED and (_HAS_FASTER_WHISPER or _HAS_WHISPER):
            try:
                text = self._transcribe_with_whisper(audio_data)
                if text:
                    LOGGER.info('Whisper transcription successful: "%s"', text)
                    return text.strip()
            except Exception as e:
                LOGGER.exception("Whisper transcription failed, falling back to Google: %s", e)

        if sr is None or self.recognizer is None:
            LOGGER.warning("SpeechRecognition is not available.")
            return ""

        try:
            with self.lock:
                audio = sr.AudioData(audio_data, SAMPLE_RATE, 2)
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8

                raw_result = self.recognizer.recognize_google(
                    audio,
                    language=RECOGNITION_LANGUAGE,
                    show_all=True,
                )
                text, confidence = self._extract_google_transcript(raw_result)
                if not text:
                    LOGGER.warning("Transcription returned no usable text")
                    return ""
                if confidence is not None and confidence < TRANSCRIPTION_CONFIDENCE_THRESHOLD:
                    LOGGER.warning(
                        "Low-confidence transcription rejected (%.2f < %.2f)",
                        confidence,
                        TRANSCRIPTION_CONFIDENCE_THRESHOLD,
                    )
                    return ""

                text = self._normalize_interview_terms(text)
                LOGGER.info("Transcription successful (%d chars)", len(text))
                LOGGER.debug('Transcript text: "%s"', text)
                return text.strip()
        except sr.UnknownValueError:
            LOGGER.warning("Speech not recognized (inaudible audio)")
            return ""
        except sr.RequestError as e:
            LOGGER.error("Transcription API error: %s", e)
            return ""
        except Exception as e:
            LOGGER.error("Transcription failed: %s", e)
            return ""

    def _extract_google_transcript(self, raw_result):
        if isinstance(raw_result, str):
            return raw_result.strip(), None

        if not isinstance(raw_result, dict):
            return "", None

        alternatives = raw_result.get("alternative") or []
        if not alternatives:
            return "", None

        best = None
        best_confidence = -1.0
        for alternative in alternatives:
            if not isinstance(alternative, dict):
                continue
            transcript = alternative.get("transcript", "").strip()
            confidence = alternative.get("confidence")
            if confidence is None:
                confidence = 0.0
            if transcript and confidence >= best_confidence:
                best = transcript
                best_confidence = confidence

        if best is None:
            return "", None

        confidence_value = None
        if best_confidence >= 0:
            confidence_value = best_confidence
            if confidence_value == 0.0 and all("confidence" not in alt for alt in alternatives):
                confidence_value = None

        return best, confidence_value

    def _normalize_interview_terms(self, text: str) -> str:
        lowered = text.lower()

        # Only correct "keyboard" when the surrounding context looks like Kubernetes.
        if "keyboard" in lowered and any(token in lowered for token in ["deployment", "stateful", "pod", "cluster", "container", "service"]):
            text = self._replace_case_insensitive(text, "keyboard", "kubernetes")

        for source, target in self._corrections:
            text = self._replace_case_insensitive(text, source, target)

        # Very common ASR confusion in interview questions.
        if "stateful state" in lowered and "stateful set" not in lowered:
            text = self._replace_case_insensitive(text, "stateful state", "stateful set")

        return text

    def _replace_case_insensitive(self, text: str, source: str, target: str) -> str:
        import re

        pattern = re.compile(rf"\b{re.escape(source)}\b", re.IGNORECASE)
        return pattern.sub(target, text)

    def _transcribe_with_whisper(self, audio_data: bytes) -> str:
        tf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        try:
            with wave.open(tf.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data)

            if _HAS_FASTER_WHISPER:
                if self._whisper_model is None:
                    LOGGER.info("Loading faster-whisper model: %s", WHISPER_MODEL)
                    self._whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
                segments, info = self._whisper_model.transcribe(tf.name, beam_size=5, language=RECOGNITION_LANGUAGE)
                return " ".join([s.text for s in segments]).strip()

            if _HAS_WHISPER:
                if self._whisper_model is None:
                    LOGGER.info("Loading openai-whisper model: %s", WHISPER_MODEL)
                    self._whisper_model = _whisper.load_model(WHISPER_MODEL)
                result = self._whisper_model.transcribe(tf.name, language=RECOGNITION_LANGUAGE)
                return result.get("text", "").strip()

            return ""
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
