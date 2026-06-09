from config import DEVOPS_COACH_MODE, LOGGER
from http_utils import http_get_json, http_post_json
from response_formatter import stream_interview_answer
from devops_knowledge_base import answer as answer_devops_question


INTERVIEW_PROMPTS = {
    "master": """You are an INTERVIEW COPILOT - an ultra-fast expert assistant designed to help during live technical interviews.

CRITICAL RULES:
1. Answer in crisp bullet points only
2. Use 3 bullets max for most questions
3. Keep each bullet under 12 words when possible
4. For coding: show only essential code snippet (5-10 lines max)
5. No intros, no filler, no long paragraphs
6. Use bullet points for multiple concepts
7. For follow-ups: ask 1-2 clarifying questions max

INTERVIEW CONTEXT:
- Questions are from technical interviewers
- Candidate needs fast, actionable answers
- Accuracy > length
- Focus on practical examples over theory

ANSWER FORMAT:
- Direct answer
- Key point
- Example if needed

Help the candidate think through the answer while staying authentic.""",
    "quick_tech": """You are a lightning-fast technical interview assistant.

TASK: Answer the interview question instantly with practical, accurate information.

RULES:
- Answer in crisp bullet points only
- Use 2-3 bullets max
- Keep each bullet short and specific
- Use examples for complex topics
- No filler or explanations unless asked

ANSWER DIRECTLY.""",
    "coding": """You are an expert coding interview assistant.

TASK: Solve the coding problem concisely and clearly.

RULES:
- Give brief explanation in 1 bullet
- Provide solution code (5-10 lines max)
- Include complexity: O(?) time and space
- Make code runnable and correct
- Explain the approach if needed

FOCUS: Correctness and clarity, not verbosity.""",
    "behavioral": """You are a behavioral interview coach.

TASK: Help craft a STAR method response (< 30 seconds when spoken).

RULES:
- Situation: 1 short bullet
- Task: 1 short bullet
- Action: 1-2 short bullets
- Result: 1 short bullet

Make it authentic and concise. No memorized answers.""",
    "system_design": """You are a system design expert for interviews.

TASK: Provide a high-level architecture design.

RULES:
- High-level overview in bullets
- 3-4 key components
- Key trade-offs
- Scalability considerations
- Be practical, not theoretical

FOCUS: Clear thinking and communication.""",
    "devops": """You are an expert DevOps Interview Coach and Senior Principal Engineer.

TASK:
- Answer DevOps interview questions with crisp, interview-ready bullets.
- Prefer the most common DevOps meaning of a term.
- If an acronym is ambiguous or uncommon, say so instead of inventing a meaning.
- Use short, precise language that sounds strong in an interview.

RULES:
- 3 bullets max for most questions.
- Each bullet should be one clear idea.
- Use: Definition, Purpose/Why it matters, Example.
- If the question is vague, answer the most likely DevOps interpretation.
- For system design, include scalability, reliability, security, and trade-offs.
- For behavioral questions, use STAR in 4 short bullets.
- For troubleshooting, include likely cause, check, fix.

NEVER:
- Invent obscure acronym expansions.
- Drift into non-DevOps meanings unless clearly intended.
- Write long paragraphs.

When the acronym is not clearly standard in DevOps, answer:
- "I don't know a standard DevOps meaning for <term>."
- "If you mean <most likely meaning>, here's the short answer..."
""",
}


class AIProviderManager:
    def __init__(self, provider="groq", api_key=None, experience_years=None):
        self.provider = provider
        self.api_key = api_key
        self.experience_years = experience_years

    def _extract_focus_term(self, text):
        lowered = text.lower().strip()
        for prefix in ("what is ", "what's ", "define ", "explain ", "tell me about "):
            if lowered.startswith(prefix):
                return text[len(prefix):].strip(" ?.")
        return text.strip(" ?.")

    def _build_system_prompt(self, text):
        focus_term = self._extract_focus_term(text)
        base_prompt = self._get_prompt_type(text)

        extra_rules = f"""

FOCUS TERM:
- Answer the exact term: {focus_term}
- Do not switch to a different product, acronym, or company
- If the term is an acronym, use the most common technical meaning
- If a phrase is ambiguous, briefly note the ambiguity and answer the most likely meaning
- Prefer definition, purpose, and one example
"""

        return base_prompt + extra_rules

    def _get_prompt_type(self, text):
        text_lower = text.lower()
        if DEVOPS_COACH_MODE:
            return INTERVIEW_PROMPTS["devops"]
        if any(word in text_lower for word in ["write", "code", "function", "algorithm", "reverse", "sort", "implement", "program"]):
            return INTERVIEW_PROMPTS["coding"]
        if any(word in text_lower for word in ["tell me about", "describe", "time you", "experience", "conflict", "failure", "challenge"]):
            return INTERVIEW_PROMPTS["behavioral"]
        if any(word in text_lower for word in ["design", "architecture", "scale", "system", "database", "service", "build"]):
            return INTERVIEW_PROMPTS["system_design"]
        return INTERVIEW_PROMPTS["quick_tech"]

    def query(self, text, callback):
        local_answer = answer_devops_question(text, experience_years=self.experience_years)
        if local_answer:
            LOGGER.debug("Answered from local DevOps knowledge base")
            return stream_interview_answer(callback, local_answer, question=text)

        result = None

        if self.provider == "groq" and self.api_key:
            LOGGER.debug("Trying Groq provider")
            result = self._query_groq(text, callback)
            if result:
                return result

        if self.provider == "openai" and self.api_key:
            LOGGER.debug("Trying OpenAI provider")
            result = self._query_openai(text, callback)
            if result:
                return result

        if self.provider == "anthropic" and self.api_key:
            LOGGER.debug("Trying Anthropic provider")
            result = self._query_anthropic(text, callback)
            if result:
                return result

        LOGGER.debug("Trying free AI provider fallback")
        result = self._query_free_ai(text, callback)
        if result:
            return result

        LOGGER.debug("Trying web AI fallback")
        result = self._query_web_ai(text, callback)
        if result:
            return result

        LOGGER.debug("Trying browser fallback")
        return self._query_google(text, callback)

    def _query_groq(self, text, callback):
        try:
            from groq_ai_provider import GroqAIProvider

            provider = GroqAIProvider(self.api_key)
            interview_prompt = self._build_system_prompt(text)
            return provider.query(text, callback, system_prompt=interview_prompt)
        except Exception as e:
            LOGGER.debug("Groq failed: %s", e)
        return None

    def _query_free_ai(self, text, callback):
        try:
            from free_ai_provider import FreeAIProvider

            provider = FreeAIProvider()
            return provider.query(text, callback)
        except Exception as e:
            LOGGER.debug("Free AI failed: %s", e)
        return None

    def _query_web_ai(self, text, callback):
        try:
            answers = []
            ddg_answer = self._get_duckduckgo_answer(text)
            if ddg_answer and len(ddg_answer) > 50:
                answers.append(ddg_answer)

            wiki_answer = self._get_wikipedia_answer(text)
            if wiki_answer and len(wiki_answer) > 50:
                answers.append(wiki_answer)

            if answers:
                best_answer = max(answers, key=len)
                LOGGER.info("Web AI answered")
                return stream_interview_answer(callback, best_answer, question=text)
        except Exception as e:
            LOGGER.debug("Web AI failed: %s", e)
        return None

    def _get_duckduckgo_answer(self, text):
        try:
            url = "https://api.duckduckgo.com/"
            params = {"q": text, "format": "json", "no_html": 1, "skip_disambig": 1}
            data = http_get_json(url, params=params, timeout=5)
            return data.get("AbstractText") or data.get("Answer") or data.get("Definition") or ""
        except Exception:
            return None

    def _get_wikipedia_answer(self, text):
        try:
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {"action": "opensearch", "search": text, "limit": 1, "format": "json"}
            search_data = http_get_json(search_url, params=search_params, timeout=5)
            if len(search_data) > 1 and len(search_data[1]) > 0:
                page_title = search_data[1][0]
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}"
                wiki_data = http_get_json(summary_url, timeout=5)
                extract = wiki_data.get("extract", "")
                if extract:
                    sentences = extract.split(". ")
                    return ". ".join(sentences[:3]) + "."
        except Exception:
            return None

    def _query_openai(self, text, callback):
        if not self.api_key:
            return self._query_google(text, callback)

        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            interview_prompt = self._build_system_prompt(text)
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": interview_prompt},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "temperature": 0.3,
                "max_tokens": 500,
            }
            response = http_post_json(url, data, headers=headers, timeout=30)
            return stream_interview_answer(callback, response["choices"][0]["message"]["content"].strip(), question=text)
        except Exception as e:
            LOGGER.error("OpenAI error: %s", e)
            return self._query_google(text, callback)

    def _query_anthropic(self, text, callback):
        if not self.api_key:
            return self._query_google(text, callback)

        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            interview_prompt = self._build_system_prompt(text)
            data = {
                "model": "claude-3-sonnet-20240229",
                "system": interview_prompt,
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 1024,
                "stream": False,
            }
            response = http_post_json(url, data, headers=headers, timeout=30)
            content_parts = []
            for part in response.get("content", []):
                if part.get("type") == "text":
                    content_parts.append(part.get("text", ""))
            content = "".join(content_parts).strip()
            return stream_interview_answer(callback, content, question=text)
        except Exception as e:
            LOGGER.error("Anthropic error: %s", e)
            return self._query_google(text, callback)

    def _query_google(self, text, callback):
        from llm_client import ChromeClient

        client = ChromeClient()
        return client.query(text, callback)

    def close(self):
        return None
