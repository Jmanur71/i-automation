import json
import time

from config import LOGGER
from http_utils import http_get_json
from response_formatter import stream_interview_answer


class ChromeClient:
    def __init__(self):
        LOGGER.info("Initializing AI client")
        self.last_request_time = 0

    def query(self, text, callback):
        try:
            LOGGER.info("Getting answer for query (%d chars)", len(text))
            LOGGER.debug('Query text: "%s"', text)

            answer = self._try_wikipedia(text)
            if not answer:
                answer = self._try_duckduckgo(text)
            if not answer:
                answer = self._try_wikipedia_alternative(text)

            if not answer:
                answer = "I couldn't find a clear answer. Try rephrasing your question."
                LOGGER.warning("No answer found from any source")
            else:
                LOGGER.info("Answer found: %s...", answer[:100])

            return stream_interview_answer(callback, answer, question=text)
        except Exception as e:
            error_msg = f"Error: {e}"
            LOGGER.error("Query exception: %s", e)
            callback(error_msg)
            return error_msg

    def _try_wikipedia(self, text):
        try:
            LOGGER.debug("Trying Wikipedia...")
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "opensearch",
                "search": text,
                "limit": 1,
                "format": "json",
            }
            search_data = http_get_json(search_url, params=search_params, timeout=5)

            if len(search_data) > 1 and len(search_data[1]) > 0:
                page_title = search_data[1][0]
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
                wiki_data = http_get_json(summary_url, timeout=5)
                extract = wiki_data.get("extract", "")
                if extract:
                    sentences = extract.split(". ")
                    result = ". ".join(sentences[:3])
                    if len(result) > 50:
                        LOGGER.info("Wikipedia answered")
                        return result + "."
        except Exception as e:
            LOGGER.debug("Wikipedia failed: %s", e)
        return None

    def _try_duckduckgo(self, text):
        try:
            LOGGER.debug("Trying DuckDuckGo...")
            url = "https://api.duckduckgo.com/"
            params = {
                "q": text,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }
            data = http_get_json(url, params=params, timeout=5)

            if data.get("AbstractText"):
                LOGGER.info("DuckDuckGo answered")
                return data["AbstractText"]
            if data.get("Answer"):
                LOGGER.info("DuckDuckGo answered")
                return data["Answer"]
            if data.get("Definition"):
                LOGGER.info("DuckDuckGo answered")
                return data["Definition"]
        except Exception as e:
            LOGGER.debug("DuckDuckGo failed: %s", e)
        return None

    def _try_huggingface(self, text):
        # Retained for compatibility; this build uses web fallbacks first.
        return None

    def _try_wikipedia_alternative(self, text):
        try:
            LOGGER.debug("Trying Wikipedia alternative search...")
            key_terms = text.lower().replace("what is", "").replace("what are", "").replace("?", "").strip()

            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": key_terms,
                "format": "json",
                "srlimit": 1,
            }
            search_data = http_get_json(search_url, params=search_params, timeout=5)

            if "query" in search_data and "search" in search_data["query"]:
                results = search_data["query"]["search"]
                if len(results) > 0:
                    page_title = results[0]["title"]
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
                    wiki_data = http_get_json(summary_url, timeout=5)
                    extract = wiki_data.get("extract", "")
                    if extract:
                        sentences = extract.split(". ")
                        result = ". ".join(sentences[:3])
                        if len(result) > 50:
                            LOGGER.info("Wikipedia alternative answered")
                            return result + "."
        except Exception as e:
            LOGGER.debug("Wikipedia alternative failed: %s", e)
        return None

    def reset(self):
        pass

    def close(self):
        LOGGER.info("Closing AI client")
