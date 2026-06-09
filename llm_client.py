from config import LOGGER
from google_search_ai import GoogleSearchAIClient
from response_formatter import stream_interview_answer


class ChromeClient:
    def __init__(self):
        LOGGER.info("Initializing Google Search AI Mode client")
        self.client = GoogleSearchAIClient()

    def query(self, text, callback):
        try:
            LOGGER.info("Getting answer for query (%d chars)", len(text))
            LOGGER.debug('Query text: "%s"', text)

            answer = self.client.query(text)

            if not answer:
                answer = "Google did not return an AI overview for this question."
                LOGGER.warning("No answer found from Google Search AI Mode or search snippets")
            else:
                LOGGER.info("Answer found: %s...", answer[:100])

            return stream_interview_answer(callback, answer, question=text)
        except Exception as e:
            error_msg = f"Error: {e}"
            LOGGER.error("Query exception: %s", e)
            callback(error_msg)
            return error_msg
    
    def close(self):
        LOGGER.info("Closing Google Search AI client")
        if self.client:
            self.client.close()
