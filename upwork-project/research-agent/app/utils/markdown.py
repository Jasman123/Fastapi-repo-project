import re

def strip_fences(text: str) -> str:

    text = text.strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)

    return text.strip()

def word_count(text: str) -> int:
    return len(text.split())

