#!/usr/bin/env python3
"""Validate the Voice Assistant setup."""

import time
import numpy as np
from config import SAMPLE_RATE, LOGGER
from audio_capture import AudioCapture
from transcription import TranscriptionEngine
from overlay_ui import OverlayUI

print("="*60)
print("VALIDATING VOICE ASSISTANT SETUP")
print("="*60)

# Test 1: AudioCapture
print("\n[1/4] Testing AudioCapture...")
try:
    audio = AudioCapture()
    print("  ✓ AudioCapture initialized")
    # Use blocking record() API which returns (trimmed, full)
    trimmed, full = audio.record(max_seconds=1)
    if full:
        print(f"  ✓ Audio captured (full): {len(full)} bytes")
        if trimmed:
            print(f"  ✓ Trimmed audio: {len(trimmed)} bytes")
    else:
        print("  ⚠ No audio data (expected if environment is silent)")
    print("  ✅ AudioCapture PASSED")
except Exception as e:
    print(f"  ❌ AudioCapture FAILED: {e}")

# Test 2: TranscriptionEngine
print("\n[2/4] Testing TranscriptionEngine...")
try:
    transcriber = TranscriptionEngine()
    print("  ✓ TranscriptionEngine initialized")
    # Create silent audio
    silence_audio = np.zeros((SAMPLE_RATE * 2,), dtype=np.int16)
    result = transcriber.transcribe(silence_audio.tobytes())
    print(f"  ✓ Transcription result: '{result}'")
    print("  ✅ TranscriptionEngine PASSED")
except Exception as e:
    print(f"  ❌ TranscriptionEngine FAILED: {e}")

# Test 3: OverlayUI
print("\n[3/4] Testing OverlayUI...")
try:
    # Don't fully run the UI, just test initialization
    ui = OverlayUI()
    print("  ✓ OverlayUI initialized")
    ui.set_status("Test Status")
    print("  ✓ Status setter works")
    ui.append_text("Test message\n")
    print("  ✓ Text appender works")
    ui.root.destroy()  # Clean up
    print("  ✅ OverlayUI PASSED")
except Exception as e:
    print(f"  ❌ OverlayUI FAILED: {e}")

# Test 4: Config & Logging
print("\n[4/4] Testing Config & Logging...")
try:
    LOGGER.info("Test log message")
    print("  ✓ Logger configured")
    print("  ✓ Imports verified")
    print("  ✅ Config & Logging PASSED")
except Exception as e:
    print(f"  ❌ Config & Logging FAILED: {e}")

print("\n" + "="*60)
print("✅ SETUP VALIDATION COMPLETE")
print("="*60)
print("\nNext steps:")
print("  1. Configure hotkey: Edit config.py if needed")
print("  2. Test Chrome (optional): Run test_chrome.py")
print("  3. Start app: Run main.py")
print("  4. Press Ctrl+Shift+Space to begin listening")
