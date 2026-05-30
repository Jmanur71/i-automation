import threading
import time
from pynput import keyboard
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from audio_capture import AudioCapture
from transcription import TranscriptionEngine
from llm_client import ChromeClient
from overlay_ui import OverlayUI
from config import HOTKEY, LOGGER

class VoiceAssistant:
    def __init__(self):
        self.audio = AudioCapture()
        self.transcriber = TranscriptionEngine()
        self.ui = OverlayUI()
        try:
            LOGGER.info('Initializing ChromeClient')
            self.chrome = ChromeClient()
        except Exception as e:
            # Surface error to UI and continue without chrome client
            self.chrome = None
            LOGGER.error(f'ChromeClient initialization failed: {e}')
            try:
                self.ui.append_text(f"[Error] ChromeClient init failed: {e}\n")
            except Exception:
                LOGGER.error(f'Failed to display ChromeClient error in UI: {e}')
        self.is_listening = False
        self.tray_icon = None
        
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
        trimmed, full = self.audio.record(max_seconds=10)
        
        if full:
            self.ui.set_status("Transcribing...")
            # Prefer trimmed audio when available, but fall back to full if
            # trimmed transcription is empty or very short.
            text = ""
            if trimmed:
                text = self.transcriber.transcribe(trimmed)
            if not text or len(text.split()) < 3:
                # try full audio as fallback
                alt = self.transcriber.transcribe(full)
                if alt and len(alt.split()) > len(text.split()):
                    text = alt

            if text:
                self.ui.append_text(f"\n[You]: {text}\n")
                self.ui.set_status("Searching Chrome...")
                
                self.ui.append_text("[Chrome]: ")
                if self.chrome:
                    self.chrome.query(text, lambda chunk: self.ui.append_text(chunk))
                else:
                    self.ui.append_text("Chrome client not available.\n")
                self.ui.append_text("\n")
        
        self.ui.set_status("Ready")
        self.is_listening = False
    
    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        
        menu = Menu(
            MenuItem('Toggle Window', lambda: self.ui.toggle_visibility()),
            MenuItem('Hide from Capture', lambda: self.ui.hide_from_capture()),
            MenuItem('Show Normal', lambda: self.ui.show_normal()),
            MenuItem('Clear Chat', lambda: self.ui.clear()),
            MenuItem('Exit', self.quit)
        )
        
        self.tray_icon = Icon("VoiceAssistant", image, "Voice Assistant", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
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
        if self.chrome:
            try:
                self.chrome.close()
            except Exception as e:
                LOGGER.warning(f'Error closing Chrome client: {e}')
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
        self.ui.set_status(f"Ready - Press {HOTKEY} to talk")
        LOGGER.info(f'Voice Assistant ready. Hotkey: {HOTKEY}')
        self.ui.run()

if __name__ == "__main__":
    app = VoiceAssistant()
    app.run()
