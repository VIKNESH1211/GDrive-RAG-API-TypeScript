from __future__ import annotations

import re

MAX_QUESTION_CHARS = 500

REFUSAL = "I can only help you with questions related to WABAG."
GREETING = "Hello! I'm WABAG's AI assistant. How can I help you today?"
NO_INFO = "I don't have information about that. I can only help you with questions related to WABAG."

_INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|prompts?|rules)",
    r"disregard (all |any )?(the )?(previous|prior|above|earlier|your) (instructions|prompts?|rules)",
    r"forget (all |everything |your )?(previous |prior )?(instructions|rules|prompts?)",
    r"(reveal|show|print|repeat|display|leak|tell me) (me )?(your |the )?(system|initial|hidden|original) (prompt|instructions?|message)",
    r"what (is|are) your (system |initial )?(prompt|instructions)",
    r"you are now\b",
    r"\bact as\b",
    r"pretend (to be|you are)",
    r"\bjailbreak\b",
    r"\bdan mode\b",
    r"developer mode",
    r"(new|override|updated) (system )?instructions?\s*:",
    r"</?\s*(system|assistant|context|question)\s*>",
    r"^\s*(system|assistant)\s*:",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE | re.MULTILINE)


def check_question(question: str) -> str | None:
    """Return a refusal message if the question must be blocked, else None."""
    if len(question) > MAX_QUESTION_CHARS:
        return f"Please keep your question under {MAX_QUESTION_CHARS} characters."
    if _INJECTION_RE.search(question):
        return REFUSAL
    return None


def sanitize_context(text: str) -> str:
    """Strip tag-like markers from retrieved text so documents can't close our delimiters."""
    return re.sub(r"</?\s*(context|question|system|assistant)\s*>", "", text, flags=re.IGNORECASE)


_GREETING_RE = re.compile(
    r"^\s*(hi+|hello+|hey+|hola|good\s+(morning|afternoon|evening)|greetings|howdy|"
    r"thanks?( you)?|thank you|ok(ay)?|bye|goodbye)(\s+(there|bot|team|all))?\s*[!.?]*\s*$",
    re.IGNORECASE,
)


def is_greeting(question: str) -> bool:
    return bool(_GREETING_RE.match(question))
