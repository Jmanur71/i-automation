import sounddevice as sd
import numpy as np
try:
    import webrtcvad
except Exception:
    webrtcvad = None

from config import SAMPLE_RATE, CHUNK_DURATION_MS, VAD_ENERGY_THRESHOLD, ENABLE_NOISE_CALIBRATION, NOISE_CALIBRATION_SECONDS, LOGGER


class AudioCapture:
    def __init__(self):
        self.chunk_ms = CHUNK_DURATION_MS
        self.sample_rate = SAMPLE_RATE
        self.frame_bytes = int(self.sample_rate * (self.chunk_ms / 1000.0)) * 2  # 2 bytes per sample
        self.noise_threshold = VAD_ENERGY_THRESHOLD
        self.vad = None
        if webrtcvad is not None:
            try:
                self.vad = webrtcvad.Vad(2)
            except Exception:
                self.vad = None

    def _pcm_from_numpy(self, data: np.ndarray) -> bytes:
        return data.astype(np.int16).tobytes()

    def _frame_generator(self, audio: np.ndarray):
        # yield 30ms frames of bytes
        bytes_per_frame = int(self.sample_rate * (self.chunk_ms / 1000.0)) * 2
        data = audio.astype(np.int16).tobytes()
        for i in range(0, len(data), bytes_per_frame):
            yield data[i:i+bytes_per_frame]

    def record(self, max_seconds=10):
        """Record up to max_seconds, then trim silence using WebRTC VAD.

        Returns a tuple: (trimmed_bytes_or_None, full_recording_bytes)
        """
        try:
            if ENABLE_NOISE_CALIBRATION:
                try:
                    LOGGER.info('Calibrating ambient noise for %s seconds', NOISE_CALIBRATION_SECONDS)
                    d = sd.rec(int(self.sample_rate * NOISE_CALIBRATION_SECONDS), samplerate=self.sample_rate, channels=1, dtype='int16')
                    sd.wait()
                    energy = np.abs(d).mean()
                    # reduce multiplier to be more sensitive in typical desktop environments
                    self.noise_threshold = max(self.noise_threshold, int(energy * 1.2))
                    LOGGER.info('Ambient noise threshold set to %s', self.noise_threshold)
                except Exception as exc:
                    LOGGER.warning('Noise calibration failed: %s', exc)

            LOGGER.info('Recording audio for up to %s seconds', max_seconds)
            audio = sd.rec(int(self.sample_rate * max_seconds), samplerate=self.sample_rate, channels=1, dtype='int16')
            sd.wait()

            audio = np.squeeze(audio)
            frames = list(self._frame_generator(audio))
            from collections import deque
            pre_roll_frames = int(600 / self.chunk_ms)  # 600ms pre-roll
            ring = deque(maxlen=pre_roll_frames)
            voiced_frames = []
            triggered = False
            silence_frames = 0
            for frame in frames:
                is_speech = False
                if self.vad is not None:
                    try:
                        is_speech = self.vad.is_speech(frame, self.sample_rate)
                    except Exception:
                        is_speech = False
                else:
                    # energy-based fallback (more sensitive)
                    try:
                        samples = np.frombuffer(frame, dtype=np.int16).astype(np.int32)
                        energy = np.abs(samples).mean()
                        # allow detection at a fraction of the calibrated noise threshold
                        is_speech = energy > (self.noise_threshold * 0.6)
                    except Exception:
                        is_speech = False

                # keep a running pre-roll buffer so we don't chop speech onset
                ring.append(frame)
                if is_speech:
                    if not triggered:
                        # include pre-roll
                        voiced_frames.extend(list(ring))
                    voiced_frames.append(frame)
                    triggered = True
                    silence_frames = 0
                else:
                    if triggered:
                        silence_frames += 1
                        # if we have a long silent tail, stop
                        if silence_frames * (self.chunk_ms / 1000.0) > 1.5:
                            break

            if voiced_frames:
                trimmed = b''.join(voiced_frames)
            else:
                trimmed = None
            full = self._pcm_from_numpy(audio)
            return (trimmed, full)

        except Exception as e:
            LOGGER.exception('Recording failed: %s', e)
            return (None, None)
