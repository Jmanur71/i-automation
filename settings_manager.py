import json
import os
from config import LOGGER

class SettingsManager:
    def __init__(self):
        self.settings_file = os.path.join(os.path.expanduser("~"), ".parakeet_settings.json")
        self.settings = self.load_settings()
    
    def load_settings(self):
        defaults = {
            "ai_provider": "groq",  # groq (fast free), openai, anthropic, google
            "groq_api_key": "",
            "hotkey": "Ctrl+Shift+Space",
            "wake_word_enabled": False,
            "wake_word": "hey parakeet",
            "auto_listen": False,
            "window_opacity": 0.95,
            "window_position": {"x": 100, "y": 100},
            "compact_mode": False,
            "always_on_top": True,
            "theme": "dark",
            "voice_feedback": False,
            "openai_api_key": "",
            "anthropic_api_key": ""
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
                    LOGGER.info('Settings loaded from file')
            except Exception as e:
                LOGGER.error(f'Failed to load settings: {e}')
        
        return defaults
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            LOGGER.info('Settings saved')
        except Exception as e:
            LOGGER.error(f'Failed to save settings: {e}')
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()
