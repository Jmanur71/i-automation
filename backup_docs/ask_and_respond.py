from audio_capture import AudioCapture
from transcription import TranscriptionEngine
from llm_client import ChromeClient

print('Please speak your question after the prompt (you have up to 10 seconds)...')
ac = AudioCapture()
trimmed, full = ac.record(max_seconds=10)
if full is None:
    print('No audio captured; aborting')
    raise SystemExit(1)

transcriber = TranscriptionEngine()
text = ''
if trimmed:
    text = transcriber.transcribe(trimmed)
if not text:
    text = transcriber.transcribe(full)

print('\nTranscribed text:', repr(text))
if not text:
    print('No transcription available; aborting')
    raise SystemExit(1)

print('\nQuerying Chrome AI...')
client = None
try:
    client = ChromeClient(headless=False)
    chunks = []
    def cb(chunk):
        chunks.append(chunk)
        print(chunk, end='')
    result = client.query(text, cb)
    print('\n\nFinal snippet:', result)
finally:
    if client:
        try:
            client.close()
        except Exception:
            pass
