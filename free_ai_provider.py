from config import LOGGER
from http_utils import http_post_json
from response_formatter import stream_interview_answer


class FreeAIProvider:
    """Free AI provider using HuggingFace Inference API."""

    def __init__(self):
        self.models = [
            "meta-llama/Llama-3.2-3B-Instruct",
            "microsoft/Phi-3-mini-4k-instruct",
            "mistralai/Mistral-7B-Instruct-v0.2",
        ]
        self.base_url = "https://api-inference.huggingface.co/models/"

    def query(self, text, callback):
        """Query free HuggingFace models."""
        for model in self.models:
            try:
                result = self._query_model(model, text, callback)
                if result and len(result) > 50:
                    LOGGER.info("AI answered via %s", model.split("/")[1])
                    return result
            except Exception as e:
                LOGGER.debug("%s failed: %s", model, e)
        return None

    def _query_model(self, model, text, callback):
        url = f"{self.base_url}{model}"
        prompt = (
            f"Answer the exact term or question using crisp bullet points only. "
            f"Do not switch to a different product, acronym, or company. "
            f"Use 2-3 bullets max, keep each bullet short and interview-friendly:\n{text}\n\nAnswer:"
        )

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False,
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False,
            },
        }

        response = http_post_json(url, payload, timeout=30)

        if isinstance(response, list) and len(response) > 0:
            answer = response[0].get("generated_text", "").strip()
        elif isinstance(response, dict):
            answer = response.get("generated_text", "").strip()
        else:
            return None

        answer = answer.replace(prompt, "").strip()
        if answer and len(answer) > 20:
            return stream_interview_answer(callback, answer, question=text)

        return None
