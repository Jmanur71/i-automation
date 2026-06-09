import requests
import json
from config import LOGGER

class GroqProvider:
    """Free, fast AI provider using Groq API"""
    
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        # This is a demo key - users should get their own from groq.com (free)
        self.api_key = "gsk_demo"
        
    def query(self, text, callback):
        """Query Groq's fast LLM API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. Provide concise, accurate answers."},
                    {"role": "user", "content": text}
                ],
                "stream": True,
                "max_tokens": 512,
                "temperature": 0.7
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, stream=True, timeout=30)
            
            if response.status_code != 200:
                LOGGER.error(f'Groq API error: {response.status_code}')
                return None
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(line)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                callback(content)
                                full_response += content
                        except:
                            pass
            
            return full_response if full_response else None
            
        except Exception as e:
            LOGGER.error(f'Groq query failed: {e}')
            return None
