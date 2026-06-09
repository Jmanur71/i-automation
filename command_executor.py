import ast
import os
import subprocess
import webbrowser
from urllib.parse import quote_plus

from config import LOGGER


class CommandExecutor:
    """Execute system commands based on voice input."""

    def __init__(self):
        self.commands = {
            "open": self.open_app,
            "search": self.web_search,
            "calculate": self.calculate,
            "time": self.get_time,
            "date": self.get_date,
        }

    def execute(self, text):
        """Parse and execute command from text."""
        text_lower = text.lower().strip()

        if not text_lower:
            return None

        if "open" in text_lower:
            app = text_lower.replace("open", "").strip()
            return self.open_app(app)

        if "search for" in text_lower or "google" in text_lower:
            query = text_lower.replace("search for", "").replace("google", "").strip()
            return self.web_search(query)

        if "calculate" in text_lower:
            expression = text_lower.replace("calculate", "").strip()
            return self.calculate(expression)

        if "time" in text_lower:
            return self.get_time()

        if "date" in text_lower:
            return self.get_date()

        return None

    def open_app(self, app_name):
        try:
            app_name = app_name.strip()
            if not app_name:
                return None

            if "chrome" in app_name or "browser" in app_name:
                webbrowser.open("https://google.com")
                return f"Opening {app_name}"
            if "notepad" in app_name:
                subprocess.Popen(["notepad.exe"])
                return "Opening Notepad"
            if "calculator" in app_name:
                subprocess.Popen(["calc.exe"])
                return "Opening Calculator"
            if os.path.exists(app_name):
                os.startfile(app_name)
                return f"Opening {app_name}"

            webbrowser.open(f"https://www.google.com/search?q={quote_plus(app_name)}")
            return f"Searching for {app_name}"
        except Exception as e:
            LOGGER.error("Failed to open %s: %s", app_name, e)
            return None

    def web_search(self, query):
        try:
            query = query.strip()
            if not query:
                return None
            webbrowser.open(f"https://google.com/search?q={quote_plus(query)}")
            return f"Searching for: {query}"
        except Exception as e:
            LOGGER.error("Web search failed: %s", e)
            return None

    def calculate(self, expression):
        try:
            value = self._safe_eval(expression)
            return f"Result: {value}"
        except Exception as e:
            LOGGER.debug("Calculation failed: %s", e)
            return None

    def _safe_eval(self, expression):
        allowed_binops = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Mod: lambda a, b: a % b,
            ast.Pow: lambda a, b: a ** b,
        }
        allowed_unary = {
            ast.UAdd: lambda a: +a,
            ast.USub: lambda a: -a,
        }

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.BinOp) and type(node.op) in allowed_binops:
                return allowed_binops[type(node.op)](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary:
                return allowed_unary[type(node.op)](_eval(node.operand))
            raise ValueError("Unsupported expression")

        parsed = ast.parse(expression, mode="eval")
        return _eval(parsed)

    def get_time(self):
        from datetime import datetime

        return f"Current time: {datetime.now().strftime('%I:%M %p')}"

    def get_date(self):
        from datetime import datetime

        return f"Today is {datetime.now().strftime('%B %d, %Y')}"
