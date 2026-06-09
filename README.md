# Voice Assistant - Parakeet AI Clone

Complete Windows desktop voice assistant with modern UI, multiple AI providers, and privacy controls.

## ✨ Key Features

### 🎤 Voice Input
- **Push-to-talk**: `Ctrl+Shift+Space` (customizable)
- **Wake word**: "Hey Parakeet" (optional)
- **Auto-listen**: Continuous mode
- **VAD-based**: Smart silence detection

### 🤖 AI Providers
- **Google Search** (no API key needed)
- **OpenAI GPT** (GPT-3.5/GPT-4)
- **Anthropic Claude** (Claude 3)
- Streaming real-time responses

### 🎨 Modern UI
- Dark professional theme
- Pulsing recording indicator
- 30-bar audio visualizer
- Color-coded status feedback
- **Compact mode**: Tiny 300x100 widget
- **Full mode**: Complete chat interface

### 🔒 Privacy Controls
- Hide to system tray
- Off-screen positioning (capture-proof)
- Always-on-top overlay
- Clear chat history

### ⚡ Voice Commands
- "Open calculator/notepad/chrome"
- "Search for [anything]"
- "What time is it?"
- "What's the date?"

### ⚙️ Settings Panel
- AI provider selection
- Window mode toggle
- API key configuration
- Hotkey customization

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Run
python main.py

# Use
Press Ctrl+Shift+Space → Speak → Get Answer
```

## Setup

```bash
pip install -r requirements.txt
python main.py
```

**Prerequisites**: Chrome browser installed

## 📖 Detailed Usage

### Basic Voice Query
1. Press `Ctrl+Shift+Space`
2. Speak your question
3. See real-time transcription
4. Get streaming AI response

### Voice Commands
```
"Open calculator"     → Launches Windows Calculator
"Search for Python"   → Opens Google search
"What time is it?"    → Shows current time
"Open notepad"        → Opens Notepad
```

### System Tray Menu
- **Toggle Window**: Show/hide main interface
- **Toggle Compact Mode**: Switch to tiny widget
- **Settings**: Open settings panel
- **Hide from Capture**: Move off-screen
- **Show Normal**: Restore window
- **Clear Chat**: Reset conversation
- **Exit**: Close app

### Settings Configuration
1. Click ⚙️ button (or right-click tray → Settings)
2. Choose AI provider:
   - **Google**: No setup needed (default)
   - **OpenAI**: Add API key to `~/.parakeet_settings.json`
   - **Anthropic**: Add API key to `~/.parakeet_settings.json`
3. Enable Compact Mode for minimal UI
4. Click Save

### API Keys (Optional)
Edit `~/.parakeet_settings.json`:
```json
{
  "ai_provider": "openai",
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-..."
}
```

## 🏗️ Architecture

```
AudioCapture (VAD) → TranscriptionEngine (Google/Whisper)
                            ↓
              CommandExecutor (Voice Commands)
                            ↓
         AIProviderManager (Google/OpenAI/Claude)
                            ↓
                  OverlayUI (Full/Compact)
                            ↑
            Controller (Hotkeys + Tray + Settings)
```

## Privacy Features

1. **Hidden Mode**: Window minimized to tray
2. **Off-screen Mode**: Window positioned at (-5000, -5000)
3. **Topmost Overlay**: Always-on-top discrete window

## 🎯 Parakeet AI Features Implemented

| Feature | Status | Implementation |
|---------|--------|----------------|
| Push-to-talk | ✅ | Ctrl+Shift+Space |
| Wake word | ✅ | Framework ready |
| Visual feedback | ✅ | Pulse + 30-bar visualizer |
| Compact mode | ✅ | 300x100 widget |
| Multiple AI | ✅ | Google/OpenAI/Claude |
| Voice commands | ✅ | Open apps, search, time |
| Settings panel | ✅ | Built-in UI |
| System tray | ✅ | Full menu |
| Privacy modes | ✅ | Hide/Off-screen/Tray |
| Streaming | ✅ | Real-time responses |
| Auto-listen | ✅ | Continuous mode |
| Hotkey custom | ✅ | Settings manager |

## 📦 Requirements

```
sounddevice>=0.5.1
SpeechRecognition>=3.12.0
requests>=2.31.0
pystray>=0.19.5
pynput>=1.7.7
Pillow>=10.0.0
scipy>=1.11.0
numpy>=1.24.0
```

## Customization

Edit `config.py`:
- `HOTKEY`: Any pynput key combination
