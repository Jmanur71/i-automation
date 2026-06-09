# Installation & Usage Guide

## 🚀 Installation

### Prerequisites
- Python 3.7+
- Windows OS
- Microphone access

### Quick Install
```bash
pip install -r requirements.txt
python main.py
```

## 🎯 How to Use

### 1. Basic Voice Query
```
1. Press Ctrl+Shift+Space
2. Speak: "What is Python?"
3. Release key
4. Get AI response
```

### 2. Voice Commands
```
"Open calculator"     → Opens Calculator
"Open notepad"        → Opens Notepad
"Search for AI"       → Google search
"What time is it?"    → Current time
"What's the date?"    → Today's date
```

### 3. System Tray
Right-click tray icon:
- Toggle Window
- Toggle Compact Mode
- Settings
- Hide from Capture
- Clear Chat
- Exit

### 4. Settings Panel
Click ⚙️ button to configure:
- AI Provider (Google/OpenAI/Claude)
- Window Mode (Full/Compact)
- Save settings

## 🔑 API Setup (Optional)

### For OpenAI
1. Get API key from https://platform.openai.com
2. Edit `~/.parakeet_settings.json`:
```json
{
  "ai_provider": "openai",
  "openai_api_key": "sk-your-key-here"
}
```

### For Anthropic Claude
1. Get API key from https://console.anthropic.com
2. Edit `~/.parakeet_settings.json`:
```json
{
  "ai_provider": "anthropic",
  "anthropic_api_key": "sk-ant-your-key-here"
}
```

## 🛠️ Troubleshooting

### Microphone Issues
- Check Windows Settings → Privacy → Microphone
- Lower `VAD_ENERGY_THRESHOLD` in config.py (try 30)
- Enable `NOISE_CALIBRATION = True`

### No Response
- Check internet connection
- Verify API keys in settings file
- Check console for error logs

### Hotkey Not Working
- Check for conflicts with other apps
- Try different key combo in config.py
- Run as administrator

### Audio Visualization Not Showing
- Normal - only shows during recording
- Press Ctrl+Shift+Space to activate

## ⚙️ Configuration

### config.py Options
```python
HOTKEY = "<ctrl>+<shift>+<space>"  # Change hotkey
VAD_ENERGY_THRESHOLD = 50           # Mic sensitivity
SAMPLE_RATE = 16000                 # Audio quality
WAKE_WORD_ENABLED = False           # Enable wake word
COMPACT_MODE = False                # Start in compact mode
```

### Settings File (~/.parakeet_settings.json)
```json
{
  "ai_provider": "google",
  "hotkey": "Ctrl+Shift+Space",
  "wake_word_enabled": false,
  "wake_word": "hey parakeet",
  "auto_listen": true,
  "window_opacity": 0.95,
  "compact_mode": false,
  "always_on_top": true,
  "openai_api_key": "",
  "anthropic_api_key": ""
}
```

## 📝 Tips

1. **Speak clearly** - Wait for red indicator
2. **Hold key** - Keep pressed while speaking
3. **Quiet environment** - Reduces background noise
4. **Compact mode** - For minimal distraction
5. **Hide from capture** - For privacy during screen sharing
