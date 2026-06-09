import requests
import json
import time
from config import LOGGER

class ChromeClient:
    def __init__(self):
        LOGGER.info('Initializing AI client')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.last_request_time = 0
        
    def query(self, text, callback):
        try:
            LOGGER.info(f'Getting answer for: "{text}"')
            
            answer = None
            
            # 1. Try Wikipedia
            answer = self._try_wikipedia(text)
            
            # 2. Try DuckDuckGo
            if not answer:
                answer = self._try_duckduckgo(text)
            
            # 3. Try alternative Wikipedia search
            if not answer:
                answer = self._try_wikipedia_alternative(text)
            
            if not answer:
                answer = "I couldn't find a clear answer. Try rephrasing your question."
                LOGGER.warning('No answer found from any source')
            else:
                LOGGER.info(f'Answer found: {answer[:100]}...')
            
            # Stream the answer
            words = answer.split()
            for i, word in enumerate(words):
                if i == 0:
                    callback(word)
                else:
                    callback(' ' + word)
            
            return answer
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            LOGGER.error(f'Query exception: {e}')
            callback(error_msg)
            return error_msg
    
    def _try_wikipedia(self, text):
        try:
            LOGGER.debug('Trying Wikipedia...')
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
                # Get page summary
                summary_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}'
                summary_response = self.session.get(summary_url, timeout=5)
                if summary_response.status_code == 200:
                    wiki_data = summary_response.json()
                    extract = wiki_data.get('extract', '')
                    if extract:
                        # Limit to first 3 sentences
                        sentences = extract.split('. ')
                        result = '. '.join(sentences[:3])
                        if len(result) > 50:
                            LOGGER.info('Wikipedia answered')
                            return result + '.'
        except Exception as e:
            LOGGER.debug(f'Wikipedia failed: {e}')
        return None
    
    def _try_duckduckgo(self, text):
        try:
            LOGGER.debug('Trying DuckDuckGo...')
            url = 'https://api.duckduckgo.com/'
            params = {
                'q': text,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            response = self.session.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get('AbstractText'):
                LOGGER.info('DuckDuckGo answered')
                return data['AbstractText']
            elif data.get('Answer'):
                LOGGER.info('DuckDuckGo answered')
                return data['Answer']
            elif data.get('Definition'):
                LOGGER.info('DuckDuckGo answered')
                return data['Definition']
        except Exception as e:
            LOGGER.debug(f'DuckDuckGo failed: {e}')
        return None
    
    def _try_huggingface(self, text):
        try:
            # Rate limiting - wait at least 2 seconds between requests
            current_time = time.time()
            if current_time - self.last_request_time < 2:
                time.sleep(2 - (current_time - self.last_request_time))
            
            LOGGER.debug('Trying Hugging Face AI...')
            url = 'https://api-inference.huggingface.co/models/google/flan-t5-large'
            payload = {
                'inputs': f'Answer concisely: {text}',
                'parameters': {
                    'max_length': 150,
                    'temperature': 0.7
                },
                'options': {'wait_for_model': True}
            }
            
            response = self.session.post(url, json=payload, timeout=20)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    answer = result[0].get('generated_text', '').strip()
                    if answer and len(answer) > 20:
                        LOGGER.info('Hugging Face AI answered')
                        return answer
            elif response.status_code == 503:
                LOGGER.debug('Hugging Face model loading...')
        except Exception as e:
            LOGGER.debug(f'Hugging Face failed: {e}')
        return None
    
    def _try_wikipedia_alternative(self, text):
        try:
            LOGGER.debug('Trying Wikipedia alternative search...')
            # Extract key terms from question
            key_terms = text.lower().replace('what is', '').replace('what are', '').replace('?', '').strip()
            
            search_url = 'https://en.wikipedia.org/w/api.php'
            search_params = {
                'action': 'query',
                'list': 'search',
                'srsearch': key_terms,
                'format': 'json',
                'srlimit': 1
            }
            search_response = self.session.get(search_url, params=search_params, timeout=5)
            search_data = search_response.json()
            
            if 'query' in search_data and 'search' in search_data['query']:
                results = search_data['query']['search']
                if len(results) > 0:
                    page_title = results[0]['title']
                    summary_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}'
                    summary_response = self.session.get(summary_url, timeout=5)
                    if summary_response.status_code == 200:
                        wiki_data = summary_response.json()
                        extract = wiki_data.get('extract', '')
                        if extract:
                            sentences = extract.split('. ')
                            result = '. '.join(sentences[:3])
                            if len(result) > 50:
                                LOGGER.info('Wikipedia alternative answered')
                                return result + '.'
        except Exception as e:
            LOGGER.debug(f'Wikipedia alternative failed: {e}')
        return None
    
    def reset(self):
        pass
    
    def close(self):
        LOGGER.info('Closing AI client')
        self.session.close()
