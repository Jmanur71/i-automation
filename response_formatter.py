import re


def _strip_markdown(text):
    text = text.replace("**", "").replace("__", "")
    text = text.replace("* ", "- ").replace("•", "-")
    return text.strip()


def format_interview_answer(text, max_bullets=4):
    text = _strip_markdown(text)
    if not text:
        return text

    if "```" in text:
        return text.strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        bullets = []
        for line in lines:
            line = re.sub(r"^[-*]\s*", "", line)
            line = re.sub(r"^\d+[\).\s-]*", "", line)
            if line:
                bullets.append(f"- {line}")
        if bullets:
            return "\n".join(bullets[:max_bullets])

    parts = re.split(r"(?<=[.!?])\s+|;\s+", text)
    parts = [part.strip(" -") for part in parts if part.strip(" -")]

    if len(parts) <= 1:
        return f"- {parts[0] if parts else text}"

    bullets = [f"- {part.rstrip('.!?')}" for part in parts[:max_bullets]]
    return "\n".join(bullets)


def looks_like_hallucinated_acronym_answer(question, answer):
    q = question.lower().strip()
    a = answer.lower().strip()
    if len(q) > 40:
        return False
    acronym_like = re.findall(r"\b(?:[A-Za-z]{2,6}(?:/[A-Za-z]{2,6})+|[A-Z]{2,6})\b", question)
    if not acronym_like and not re.search(r"\b(?:[a-z]\s+){2,5}[a-z]\b", q):
        return False
    if any(phrase in a for phrase in ["i don't know a standard", "if you mean", "ambiguous"]):
        return False
    if any(phrase in a for phrase in ["stands for", "is a", "refers to"]):
        return True
    return False


def stream_interview_answer(callback, text, question=None):
    formatted = format_interview_answer(text)
    if not formatted:
        return ""

    lines = formatted.splitlines()
    for i, line in enumerate(lines):
        if i == 0:
            callback(line)
        else:
            callback("\n" + line)
    return formatted
