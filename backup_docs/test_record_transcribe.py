from audio_capture import AudioCapture
from transcription import TranscriptionEngine

print('Recording 5 seconds (speak now)...')
ac = AudioCapture()
trimmed, full = ac.record(max_seconds=5)
if full is None:
    print('No data captured')
else:
    print('Captured bytes (full):', len(full))
    if trimmed:
        print('Captured bytes (trimmed):', len(trimmed))
    t = TranscriptionEngine()
    # Prefer trimmed audio for speed/accuracy but fall back to full if needed
    text = ''
    if trimmed:
        text = t.transcribe(trimmed)
    if not text:
        text = t.transcribe(full)
    print('Transcription:', repr(text))
