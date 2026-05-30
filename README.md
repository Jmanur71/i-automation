# Voice Assistant - Real-time STT to Chrome Search

Minimal Windows desktop app for voice-to-Google search with privacy modes.

## Setup

```bash
pip install -r requirements.txt
python main.py
```

**Prerequisites**: Chrome browser installed

## Usage

- **Hotkey**: `Ctrl+Shift+Space` - Toggle listening
- **System Tray**: Right-click for options
  - Toggle Window - Show/hide UI
  - Hide from Capture - Move window off-screen
  - Show Normal - Restore window position
  - Clear Chat - Reset conversation

## Architecture

```
AudioCapture (VAD) → TranscriptionEngine (Whisper) → ChromeClient (Google) → OverlayUI
                              ↓
                         Controller (Hotkeys + Tray)
```

## Privacy Features

1. **Hidden Mode**: Window minimized to tray
2. **Off-screen Mode**: Window positioned at (-5000, -5000)
3. **Topmost Overlay**: Always-on-top discrete window

## Performance

- Google Speech Recognition for transcription (no local model needed)
- VAD filters silence before transcription
- Async audio processing thread

## Customization

Edit `config.py`:
- `HOTKEY`: Any pynput key combination
