import threading

import numpy as np

from config import ENABLE_NOISE_CALIBRATION, LOGGER, NOISE_CALIBRATION_SECONDS, SAMPLE_RATE, VAD_ENERGY_THRESHOLD, CHUNK_DURATION_MS

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import webrtcvad
except Exception:
    webrtcvad = None


class AudioCapture:
    def __init__(self):
        self.chunk_ms = CHUNK_DURATION_MS
        self.sample_rate = SAMPLE_RATE
        self.frame_bytes = int(self.sample_rate * (self.chunk_ms / 1000.0)) * 2
        self.noise_threshold = VAD_ENERGY_THRESHOLD
        self.vad = None
        self.silence_timeout_seconds = 3.2
        if webrtcvad is not None:
            try:
                self.vad = webrtcvad.Vad(2)
            except Exception:
                self.vad = None

    def _pcm_from_numpy(self, data: np.ndarray) -> bytes:
        return data.astype(np.int16).tobytes()

    def _frame_generator(self, audio: np.ndarray):
        bytes_per_frame = int(self.sample_rate * (self.chunk_ms / 1000.0)) * 2
        data = audio.astype(np.int16).tobytes()
        for i in range(0, len(data), bytes_per_frame):
            yield data[i : i + bytes_per_frame]

    def record(self, max_seconds=10):
        """Record up to max_seconds, then trim silence using WebRTC VAD."""
        if sd is None:
            LOGGER.warning("Audio capture backend is not available.")
            return (None, None)

        try:
            if ENABLE_NOISE_CALIBRATION:
                try:
                    LOGGER.info("Calibrating ambient noise for %s seconds", NOISE_CALIBRATION_SECONDS)
                    d = sd.rec(int(self.sample_rate * NOISE_CALIBRATION_SECONDS), samplerate=self.sample_rate, channels=1, dtype="int16")
                    sd.wait()
                    energy = np.abs(d).mean()
                    self.noise_threshold = max(50, int(energy * 1.5))
                    LOGGER.info("Ambient noise threshold set to %s", self.noise_threshold)
                except Exception as exc:
                    LOGGER.warning("Noise calibration failed: %s", exc)

            LOGGER.info("Recording audio for up to %s seconds", max_seconds)
            audio = sd.rec(int(self.sample_rate * max_seconds), samplerate=self.sample_rate, channels=1, dtype="int16")
            sd.wait()

            audio = np.squeeze(audio)
            frames = list(self._frame_generator(audio))
            from collections import deque

            pre_roll_frames = int(500 / self.chunk_ms)
            ring = deque(maxlen=pre_roll_frames)
            voiced_frames = []
            triggered = False
            silence_frames = 0
            voiced_frame_count = 0
            min_voiced_frames_before_stop = int(0.75 / (self.chunk_ms / 1000.0))

            for frame in frames:
                is_speech = False
                if self.vad is not None:
                    try:
                        is_speech = self.vad.is_speech(frame, self.sample_rate)
                    except Exception:
                        is_speech = False
                else:
                    try:
                        samples = np.frombuffer(frame, dtype=np.int16).astype(np.int32)
                        energy = np.abs(samples).mean()
                        is_speech = energy > (self.noise_threshold * 0.4)
                    except Exception:
                        is_speech = False

                ring.append(frame)
                if is_speech:
                    if not triggered:
                        voiced_frames.extend(list(ring))
                    voiced_frames.append(frame)
                    triggered = True
                    voiced_frame_count += 1
                    silence_frames = 0
                elif triggered:
                    voiced_frames.append(frame)
                    silence_frames += 1
                    if voiced_frame_count >= min_voiced_frames_before_stop and silence_frames * (self.chunk_ms / 1000.0) > self.silence_timeout_seconds:
                        break

            trimmed = b"".join(voiced_frames) if voiced_frames else None
            full = self._pcm_from_numpy(audio)
            return (trimmed, full)
        except Exception as e:
            LOGGER.exception("Recording failed: %s", e)
            return (None, None)
