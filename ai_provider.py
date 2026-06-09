import requests
import json
from config import LOGGER

class AIProviderManager:
    def __init__(self, provider="groq", api_key=None):
        self.provider = provider
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
    
    def query(self, text, callback):
        # Priority order: Groq (fast & accurate) -> OpenAI -> Anthropic -> Free alternatives
        result = None
        
        # 1. Try Groq (best free option - fast and accurate)
        if self.provider == "groq" or not self.api_key:
            result = self._query_groq(text, callback)
            if result:
                return result
        
        # 2. Try paid APIs if configured
        if self.provider == "openai" and self.api_key:
            result = self._query_openai(text, callback)
            if result:
                return result
        elif self.provider == "anthropic" and self.api_key:
            result = self._query_anthropic(text, callback)
            if result:
                return result
        
        # 3. Fallback to free HuggingFace models
        result = self._query_free_ai(text, callback)
        if result:
            return result
        
        # 4. Final fallback to web search
        return self._query_google(text, callback)
    
    def _query_groq(self, text, callback):
        """Use Groq's fast and accurate Llama models"""
        try:
            from groq_ai_provider import GroqAIProvider
            groq_key = self.api_key if self.provider == "groq" else None
            provider = GroqAIProvider(groq_key)
            result = provider.query(text, callback)
            if result:
                return result
        except Exception as e:
            LOGGER.debug(f'Groq failed: {e}')
        return None
    
    def _query_free_ai(self, text, callback):
        """Try free AI models from HuggingFace"""
        try:
            from free_ai_provider import FreeAIProvider
            provider = FreeAIProvider()
            result = provider.query(text, callback)
            if result:
                return result
        except Exception as e:
            LOGGER.debug(f'Free AI failed: {e}')
        return None
    
    def _query_web_ai(self, text, callback):
        """Aggregate answers from Wikipedia and DuckDuckGo for better results"""
        try:
            answers = []
            
            # Get DuckDuckGo instant answer
            ddg_answer = self._get_duckduckgo_answer(text)
            if ddg_answer and len(ddg_answer) > 50:
                answers.append(ddg_answer)
            
            # Get Wikipedia summary
            wiki_answer = self._get_wikipedia_answer(text)
            if wiki_answer and len(wiki_answer) > 50:
                answers.append(wiki_answer)
            
            if answers:
                # Use the longest, most detailed answer
                best_answer = max(answers, key=len)
                LOGGER.info('Web AI answered')
                # Stream the answer
                words = best_answer.split()
                for i, word in enumerate(words):
                    callback(word if i == 0 else ' ' + word)
                return best_answer
                
        except Exception as e:
            LOGGER.debug(f'Web AI failed: {e}')
        return None
    
    def _get_duckduckgo_answer(self, text):
        try:
            url = 'https://api.duckduckgo.com/'
            params = {'q': text, 'format': 'json', 'no_html': 1, 'skip_disambig': 1}
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            
            return (data.get('AbstractText') or data.get('Answer') or 
                    data.get('Definition') or '')
        except:
            return None
    
    def _get_wikipedia_answer(self, text):
        try:
            # Search Wikipedia
            search_url = 'https://en.wikipedia.org/w/api.php'
            search_params = {
                'action': 'opensearch',
                'search': text,
                'limit': 1,
                'format': 'json'
            }
            search_response = self.session.get(search_url, params=search_params, timeout=5)
            search_data = search_response.json()
            
            if len(search_data) > 1 and len(search_data[1]) > 0:
                page_title = search_data[1][0]
                summary_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}'
                summary_response = self.session.get(summary_url, timeout=5)
                if summary_response.status_code == 200:
                    wiki_data = summary_response.json()
                    extract = wiki_data.get('extract', '')
                    if extract:
                        sentences = extract.split('. ')
                        return '. '.join(sentences[:3]) + '.'
        except:
            return None
    
    def _query_openai(self, text, callback):
        if not self.api_key:
            return self._query_google(text, callback)
        
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": text}],
                "stream": True
            }
            
            response = self.session.post(url, headers=headers, json=data, stream=True)
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line == '[DONE]':
                            break
                        try:
                            chunk = json.loads(line)
                            content = chunk['choices'][0]['delta'].get('content', '')
                            if content:
                                callback(content)
                                full_response += content
                        except:
                            pass
            
            return full_response
        except Exception as e:
            LOGGER.error(f'OpenAI error: {e}')
            return self._query_google(text, callback)
    
    def _query_anthropic(self, text, callback):
        if not self.api_key:
            return self._query_google(text, callback)
        
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            data = {
                "model": "claude-3-sonnet-20240229",
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 1024,
                "stream": True
            }
            
            response = self.session.post(url, headers=headers, json=data, stream=True)
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            chunk = json.loads(line[6:])
                            if chunk['type'] == 'content_block_delta':
                                content = chunk['delta'].get('text', '')
                                if content:
                                    callback(content)
                                    full_response += content
                        except:
                            pass
            
            return full_response
        except Exception as e:
            LOGGER.error(f'Anthropic error: {e}')
            return self._query_google(text, callback)
    
    def _query_google(self, text, callback):
        # Use the original ChromeClient implementation
        from llm_client import ChromeClient
        client = ChromeClient()
        return client.query(text, callback)
