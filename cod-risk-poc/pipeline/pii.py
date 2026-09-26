"""Strip phone numbers and self-declared names before any text reaches the LLM."""
import re

# Tunisian mobile/landline: 8 digits starting 2/3/4/5/7/9, optional +216/00216, optional separators.
_PHONE = re.compile(
    r"(?<!\d)(?:(?:\+|00)\s?216[\s.-]?)?[234579]\d(?:[\s.-]?\d){6}(?!\d)"
)
# "esmi Ahmed", "je m'appelle Ahmed Ben Ali", "nom: Ahmed", "اسمي أحمد"
_NAME_CUES = re.compile(
    r"(?i)\b(esmi|ismi|je m'appelle|je m appelle|mon nom est|nom\s*:|name\s*:)\s+"
    r"([A-Za-zÀ-ÿ]+(?:\s+(?:ben\s+)?[A-Z][A-Za-zÀ-ÿ]+)?)"
)
_NAME_CUES_AR = re.compile(r"(اسمي|إسمي)\s+([؀-ۿ]+)")


def strip_pii(text: str) -> str:
    if not text:
        return ""
    text = _PHONE.sub("[PHONE]", text)
    text = _NAME_CUES.sub(lambda m: f"{m.group(1)} [NAME]", text)
    text = _NAME_CUES_AR.sub(lambda m: f"{m.group(1)} [NAME]", text)
    return text
