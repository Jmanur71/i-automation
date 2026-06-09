import threading
import time
from pynput import keyboard
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from audio_capture import AudioCapture
from transcription import TranscriptionEngine
from ai_provider import AIProviderManager
from overlay_ui import OverlayUI
from settings_manager import SettingsManager
from wake_word import WakeWordDetector
from command_executor import CommandExecutor
from config import HOTKEY, LOGGER

# ⚡ INTERVIEW COPILOT MODE ENABLED
# Using ULTIMATE_INTERVIEW_PROMPT setup with optimized prompts for:
# - Quick Technical Q&A
# - Coding Challenges  
# - Behavioral Questions
# - System Design Questions
# 500% FASTER MODE: Ultra-fast inference with optimized settings
INTERVIEW_COPILOT_MODE = True

class VoiceAssistant:
    def __init__(self):
        self.settings = SettingsManager()
        self.audio = AudioCapture()
        self.transcriber = TranscriptionEngine()
        self.ui = OverlayUI(self.settings)
        self.command_executor = CommandExecutor()
        
        # Log Interview Copilot initialization
        from config import ULTRA_FAST_MODE, MAX_AI_TOKENS, AI_TEMPERATURE
        LOGGER.info('🎯 INTERVIEW COPILOT ACTIVATED - 500% FASTER MODE 🚀')
        LOGGER.info('✨ Features: Auto-detect (Quick Tech, Coding, Behavioral, System Design)')
        LOGGER.info(f'⚡ Ultra-Fast: {ULTRA_FAST_MODE} | Tokens: {MAX_AI_TOKENS} | Temp: {AI_TEMPERATURE} | Response: <2s')
        
        # Initialize AI provider based on settings
        provider = self.settings.get('ai_provider', 'groq')
        api_key = None
        if provider == 'groq':
            api_key = self.settings.get('groq_api_key')
        elif provider == 'openai':
            api_key = self.settings.get('openai_api_key')
        elif provider == 'anthropic':
            api_key = self.settings.get('anthropic_api_key')
        
        try:
            LOGGER.info(f'Initializing AI Provider: {provider}')
            self.ai = AIProviderManager(provider, api_key)
        except Exception as e:
            self.ai = None
            LOGGER.error(f'AI Provider initialization failed: {e}')
            try:
                self.ui.append_text(f"[Error] AI init failed: {e}\n")
            except Exception:
                LOGGER.error(f'Failed to display AI error in UI: {e}')
        
        self.is_listening = False
        self.tray_icon = None
        self.wake_word_detector = None
    
    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        self.is_listening = True
        self.ui.set_status("🎤 Listening...")
        threading.Thread(target=self._process_audio, daemon=True).start()
    
    def stop_listening(self):
        self.is_listening = False
        self.ui.set_status("Processing...")
        # AudioCapture.record() is blocking and runs in the background thread.
        # We don't have a synchronous stop API; just mark as not listening
        # and let the background thread finish processing.
        LOGGER.debug('Stop requested; background recording will finish naturally')
    
    def _process_audio(self):
        # Record using VAD-based endpoint detection (blocking up to max seconds)
        from config import MAX_RECORDING_SECONDS, ULTRA_FAST_MODE
        trimmed, full = self.audio.record(max_seconds=MAX_RECORDING_SECONDS)  # Ultra-fast: 3 seconds max
        
        if full:
            self.ui.set_status("⏳ Transcribing...")
            # Use trimmed audio for faster transcription (faster response in interview mode)
            text = ""
            if trimmed:
                text = self.transcriber.transcribe(trimmed)
                if not ULTRA_FAST_MODE:
                    LOGGER.info(f'Transcription: "{text}"')

            if text:
                self.ui.append_text(f"\n🗣️ You: {text}\n", "user")
                
                # Try to execute as command first
                cmd_result = self.command_executor.execute(text)
                if cmd_result:
                    self.ui.append_text(f"✅ {cmd_result}\n\n", "chrome")
                    self.ui.set_status("✅ Ready - Press Ctrl+Shift+Space")
                    self.is_listening = False
                    return
                
                self.ui.set_status("💡 Thinking...")
                from config import ULTRA_FAST_MODE
                if not ULTRA_FAST_MODE:
                    LOGGER.info(f'Querying AI with: "{text}"')
                
                self.ui.append_text("🤖 Assistant: ", "chrome")
                if self.ai:
                    try:
                        result = self.ai.query(text, lambda chunk: self.ui.append_text(chunk, "chrome"))
                        if not ULTRA_FAST_MODE:
                            LOGGER.info(f'Query completed: {result[:100] if result else "No result"}')
                    except Exception as e:
                        if not ULTRA_FAST_MODE:
                            LOGGER.error(f'Query failed: {e}')
                        self.ui.append_text(f"Error: {e}\n", "error")
                else:
                    self.ui.append_text("API provider not available.\n", "error")
                    if not ULTRA_FAST_MODE:
                        LOGGER.warning('AI provider is None')
                self.ui.append_text("\n")
            else:
                from config import ULTRA_FAST_MODE
                self.ui.set_status("⚠️ No speech detected - Try again")
                if not ULTRA_FAST_MODE:
                    LOGGER.warning('No text transcribed from audio')
        
        self.ui.set_status("✅ Ready - Press Ctrl+Shift+Space")
        self.is_listening = False
    
    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        
        menu = Menu(
            MenuItem('Toggle Window', lambda: self.ui.toggle_visibility()),
            MenuItem('Toggle Compact Mode', lambda: self.toggle_compact_mode()),
            MenuItem('Settings', lambda: self.ui.open_settings()),
            MenuItem('Hide from Capture', lambda: self.ui.hide_from_capture()),
            MenuItem('Show Normal', lambda: self.ui.show_normal()),
            MenuItem('Clear Chat', lambda: self.ui.clear()),
            MenuItem('Exit', self.quit)
        )
        
        self.tray_icon = Icon("VoiceAssistant", image, "Voice Assistant", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def toggle_compact_mode(self):
        current = self.settings.get('compact_mode', False)
        self.settings.set('compact_mode', not current)
        LOGGER.info(f'Compact mode: {not current}. Restart app to apply.')
    
    def setup_hotkey(self):
        def on_activate():
            self.toggle_listening()
        
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(HOTKEY),
            on_activate
        )
        
        def for_canonical(f):
            return lambda k: f(listener.canonical(k))
        
        listener = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)
        )
        listener.start()
    
    def quit(self):
        LOGGER.info('Shutting down Voice Assistant')
        if self.wake_word_detector:
            self.wake_word_detector.stop()
        if self.ai:
            try:
                if hasattr(self.ai, 'close'):
                    self.ai.close()
            except Exception as e:
                LOGGER.warning(f'Error closing AI provider: {e}')
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception as e:
                LOGGER.warning(f'Error stopping tray icon: {e}')
        try:
            self.ui.root.quit()
        except Exception as e:
            LOGGER.warning(f'Error quitting UI: {e}')
    
    def run(self):
        LOGGER.info('Starting Voice Assistant')
        self.create_tray_icon()
        self.setup_hotkey()
        self.ui.set_status("✅ Ready - Press Ctrl+Shift+Space to talk")
        LOGGER.info('Voice Assistant ready - Push-to-talk enabled')
        self.ui.run()

if __name__ == "__main__":
    app = VoiceAssistant()
    app.run()
