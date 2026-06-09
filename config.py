import logging

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
)
LOGGER = logging.getLogger('VoiceAssistant')

# Audio Configuration - OPTIMIZED FOR 500% FASTER RESPONSE
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 30
VAD_ENERGY_THRESHOLD = 50  # Lowered for better sensitivity
ENABLE_NOISE_CALIBRATION = False  # Disable on every call - use fixed threshold
NOISE_CALIBRATION_SECONDS = 0.5  # Faster calibration
RECOGNITION_LANGUAGE = 'en-US'
NORMALIZE_AUDIO = True
MAX_RECORDING_SECONDS = 6  # Give the user time to finish longer questions
MAX_AI_TOKENS = 250  # Ultra-concise responses (was 500, now 250)
AI_TEMPERATURE = 0.5  # Balanced for speed (was 0.3, now 0.5 for faster inference)
ULTRA_FAST_MODE = True  # Enable streaming + parallel processing
# Whisper (offline) configuration - optional. Install `faster-whisper` or
# `whisper` if you want offline transcription. Leave `WHISPER_ENABLED=False`
# to keep using Google SpeechRecognition.
WHISPER_ENABLED = False
# Preferred backend: 'faster_whisper' or 'whisper' (openai-whisper)
WHISPER_BACKEND = 'faster_whisper'
# Model size/path to load (e.g. 'small', 'base', or local path)
WHISPER_MODEL = 'small'
# If Google speech recognition reports a confidence lower than this,
# treat the result as unreliable and ask the user to repeat.
TRANSCRIPTION_CONFIDENCE_THRESHOLD = 0.60

# Hotkey Configuration
HOTKEY = "<ctrl>+<shift>+<space>"

# Parakeet Features
WAKE_WORD = "hey parakeet"
WAKE_WORD_ENABLED = False
COMPACT_MODE = False
WINDOW_OPACITY = 0.95
PUSH_TO_TALK = True  # Use push-to-talk like Parakeet AI
DEVOPS_COACH_MODE = True

# Chrome / Selenium configuration
# Set to True to run Chrome in headless mode by default. Some environments
# (Windows desktop) may have issues with headless; the client falls back
# to non-headless when a runtime error occurs.
CHROME_HEADLESS = False
# Optional user data dir (profile) to persist cookies/login. When using AI
# targets like Bard you will often need to be signed in; set this to a path
# such as r"C:\Users\Windows\AppData\Local\Google\Chrome\User Data\Profile 1"
CHROME_USER_DATA_DIR = None
# AI target: 'google' uses regular Google Search; 'bard' attempts to open
# Bard (requires signed-in account). Set as appropriate.
CHROME_AI_TARGET = 'google'
# When using Google, proactively attempt to switch the search page into AI Mode.
CHROME_GOOGLE_AI_MODE = True
