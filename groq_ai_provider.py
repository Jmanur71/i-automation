from config import LOGGER
from http_utils import http_post_json
from response_formatter import stream_interview_answer


class GroqAIProvider:
    """Groq AI provider using Llama models - fast and accurate."""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.models = [
            "llama-3.1-8b-instant",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
        ]

    def query(self, text, callback, model_index=0, system_prompt=None):
        """Query Groq's fast LLM API."""
        try:
            if not self.api_key:
                LOGGER.debug("Groq API key not configured")
                return None

            model = self.models[model_index] if model_index < len(self.models) else self.models[0]
            system_content = system_prompt or (
                "You are a helpful AI assistant. Answer in crisp bullet points only. "
                "Use at most 3 bullets unless the user asks for more. "
                "Keep each bullet short, specific, and interview-ready."
            )

            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "temperature": 0.5,
                "max_tokens": 250,
            }

            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = http_post_json(self.api_url, data, headers=headers, timeout=30)

            content = ""
            try:
                content = response["choices"][0]["message"]["content"].strip()
            except Exception:
                content = ""

            if content:
                return stream_interview_answer(callback, content, question=text)

            return None
        except Exception as e:
            LOGGER.error("Groq query failed: %s", e)
            if model_index < len(self.models) - 1:
                return self.query(text, callback, model_index + 1, system_prompt=system_prompt)
            return None
