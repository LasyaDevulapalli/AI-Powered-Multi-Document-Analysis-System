import re
from typing import List


_ACTION_VERBS = (
    "calculate|compute|derive|compare|explain|describe|state|show|list|"
    "identify|find|give|prove|determine|summarize|discuss|evaluate|solve"
)
_CACHE_MAPPING_TERMS = (
    (r"\bdirect(?:[-\s]+mapped|\s+mapping)\b", "direct mapped cache"),
    (r"\bfully\s+associative\b", "fully associative cache"),
    (r"\bset[-\s]+associative\b", "set associative cache"),
)


def decompose_question(question: str) -> List[str]:
    """Split explicit subquestions while retaining the original as retrieval context."""
    text = (question or "").strip()
    if not text:
        return []

    if "cache" in text.casefold():
        cache_components = [
            retrieval_phrase
            for pattern, retrieval_phrase in _CACHE_MAPPING_TERMS
            if re.search(pattern, text, flags=re.IGNORECASE)
        ]
        if len(cache_components) == len(_CACHE_MAPPING_TERMS):
            return [text, *cache_components][:6]

    segments = [
        item.strip(" \t\r\n;?")
        for item in re.split(r"(?:\r?\n+|;|\?(?=\s|$))", text)
        if item.strip(" \t\r\n;?")
    ]
    if len(segments) == 1:
        action_parts = re.split(
            rf"\b(?:and|then|also|additionally)\s+(?=(?:{_ACTION_VERBS})\b)",
            text,
            flags=re.IGNORECASE,
        )
        if len(action_parts) > 1:
            segments = [item.strip(" \t\r\n;?") for item in action_parts]

    if len(segments) <= 1:
        return [text]

    result = []
    seen = set()
    for candidate in [text, *segments]:
        normalized = re.sub(r"\s+", " ", candidate).strip()
        key = normalized.casefold()
        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)
        if len(result) == 6:
            break
    return result
