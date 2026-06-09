import os
import webbrowser
import subprocess
from config import LOGGER

class CommandExecutor:
    """Execute system commands based on voice input"""
    
    def __init__(self):
        self.commands = {
            'open': self.open_app,
            'search': self.web_search,
            'calculate': self.calculate,
            'time': self.get_time,
            'date': self.get_date,
        }
    
    def execute(self, text):
        """Parse and execute command from text"""
        text_lower = text.lower()
        
        # Open applications
        if 'open' in text_lower:
            app = text_lower.replace('open', '').strip()
            return self.open_app(app)
        
        # Web search
        if 'search for' in text_lower or 'google' in text_lower:
            query = text_lower.replace('search for', '').replace('google', '').strip()
            return self.web_search(query)
        
        # Time/Date
        if 'time' in text_lower:
            return self.get_time()
        if 'date' in text_lower:
            return self.get_date()
        
        return None
    
    def open_app(self, app_name):
        try:
            if 'chrome' in app_name or 'browser' in app_name:
                webbrowser.open('https://google.com')
                return f"Opening {app_name}"
            elif 'notepad' in app_name:
                subprocess.Popen(['notepad.exe'])
                return "Opening Notepad"
            elif 'calculator' in app_name:
                subprocess.Popen(['calc.exe'])
                return "Opening Calculator"
            else:
                os.startfile(app_name)
                return f"Opening {app_name}"
        except Exception as e:
            LOGGER.error(f'Failed to open {app_name}: {e}')
            return None
    
    def web_search(self, query):
        try:
            webbrowser.open(f'https://google.com/search?q={query}')
            return f"Searching for: {query}"
        except Exception as e:
            LOGGER.error(f'Web search failed: {e}')
            return None
    
    def calculate(self, expression):
        try:
            result = eval(expression)
            return f"Result: {result}"
        except:
            return None
    
    def get_time(self):
        from datetime import datetime
        return f"Current time: {datetime.now().strftime('%I:%M %p')}"
    
    def get_date(self):
        from datetime import datetime
        return f"Today is {datetime.now().strftime('%B %d, %Y')}"
