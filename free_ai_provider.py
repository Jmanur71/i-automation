import requests
import json
from config import LOGGER

class FreeAIProvider:
    """Free AI provider using HuggingFace Inference API"""
    
    def __init__(self):
        self.models = [
            "meta-llama/Llama-3.2-3B-Instruct",
            "microsoft/Phi-3-mini-4k-instruct",
            "mistralai/Mistral-7B-Instruct-v0.2"
        ]
        self.base_url = "https://api-inference.huggingface.co/models/"
    
    def query(self, text, callback):
        """Query free HuggingFace models"""
        for model in self.models:
            try:
                result = self._query_model(model, text, callback)
                if result and len(result) > 50:
                    LOGGER.info(f'AI answered via {model.split("/")[1]}')
                    return result
            except Exception as e:
                LOGGER.debug(f'{model} failed: {e}')
                continue
        
        return None
    
    def _query_model(self, model, text, callback):
        """Query a specific HuggingFace model"""
        url = f"{self.base_url}{model}"
        headers = {"Content-Type": "application/json"}
        
        # Format prompt for instruction models
        prompt = f"Answer this question concisely and accurately: {text}\n\nAnswer:"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                answer = data[0].get('generated_text', '').strip()
            elif isinstance(data, dict):
                answer = data.get('generated_text', '').strip()
            else:
                return None
            
            # Clean up the answer
            answer = answer.replace(prompt, '').strip()
            
            if answer and len(answer) > 20:
                # Stream the response
                words = answer.split()
                for i, word in enumerate(words):
                    callback(word if i == 0 else ' ' + word)
                return answer
        
        return None
