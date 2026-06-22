import re

def clean_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)

    boilerplate_patterns = [
        r"we use cookies.*",
        r"accept all cookies.*",
        r"privacy policy.*",
        r"cookie policy.*",
        r"gdpr.*",
        r"subscribe to our newsletter.*",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    
    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"[^\x20-\x7E\n]", "", text)

    return text.strip()

def truncate_for_llm(text: str, max_chars: int = 6000) -> str:
    """
    Truncates text to fit within LLM context window.
    Cuts from the end — the most important info is usually at the top.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[... truncated for length ...]"


def extract_emails_from_text(text: str) -> list[str]:
    """
    Regex fallback for finding email addresses in raw text.
    Used when LLM extraction misses the contact email.
    """
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    found = re.findall(pattern, text)

    # Filter out common non-contact emails
    noise = {"noreply", "no-reply", "support", "info", "hello", "admin"}
    filtered = [
        e for e in found
        if not any(n in e.lower() for n in noise)
    ]

    return list(set(filtered))  # deduplicate

