import requests
import json
from config import LOGGER

class GroqAIProvider:
    """Groq AI provider using Llama models - Fast and accurate"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or "gsk_demo"  # Users should get free key from console.groq.com
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.models = [
            "llama-3.1-8b-instant",  # Ultra-fast
            "llama3-8b-8192",        # Balanced
            "mixtral-8x7b-32768"     # High quality
        ]
    
    def query(self, text, callback, model_index=0, system_prompt=None):
        """Query Groq's fast LLM API with streaming"""
        try:
            model = self.models[model_index] if model_index < len(self.models) else self.models[0]
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Use provided system prompt or default
            system_content = system_prompt or "You are a helpful AI assistant. Provide clear, accurate, and concise answers. For technical questions, be specific and detailed."
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "stream": True,
                "temperature": 0.5,
                "max_tokens": 250
            }
            
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=data, 
                stream=True, 
                timeout=30
            )
            
            if response.status_code == 401:
                LOGGER.error('Groq API key invalid. Get free key from console.groq.com')
                return None
            
            if response.status_code != 200:
                LOGGER.error(f'Groq API error: {response.status_code}')
                return None
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line_data = line[6:]
                        if line_data.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(line_data)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                callback(content)
                                full_response += content
                        except json.JSONDecodeError:
                            continue
            
            if full_response:
                from config import ULTRA_FAST_MODE
                if not ULTRA_FAST_MODE:
                    LOGGER.info(f'Groq answered with {model}')
                return full_response
            
            return None
            
        except Exception as e:
            LOGGER.error(f'Groq query failed: {e}')
            # Try next model
            if model_index < len(self.models) - 1:
                return self.query(text, callback, model_index + 1)
            return None
