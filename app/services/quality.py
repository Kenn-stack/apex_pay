import re
from app.schemas.ticket import QualityReport


def check_html_and_markup(text: str) -> tuple[bool, str]:
    """Dimension 1a. Returns (found: bool, cleaned_text: str).
    TODO: research a regex or simple string search for tags like <script>, <div>, <img
    TODO: if found, strip them out and return the cleaned version
    """
    tag_pattern = re.compile(r"<!--.*?-->|<[^>]*>", re.DOTALL)
    found = bool(tag_pattern.search(text))
    cleaned_text = tag_pattern.sub("", text).strip()

    return found, cleaned_text


def normalize_whitespace(text: str) -> tuple[bool, str]:
    """Dimension 1b. Detect excessive whitespace, then normalize it.

    Returns (was_excessive: bool, cleaned_text: str).
    """
    # 1. Strip leading and trailing whitespace first
    stripped = text.strip()

    # 2. Collapse any sequence of 2 or more whitespace characters into a single space
    cleaned_text = re.sub(r"\s{2,}", " ", stripped)

    # 3. Detect if the original text needed any normalization
    was_excessive = text != cleaned_text

    return was_excessive, cleaned_text

def check_shouting(text: str) -> bool:
    """Dimension 2a. True if len(text) > 30 AND >60% of alphabetic chars are uppercase."""
    # 1. Check overall length condition
    if len(text) <= 30:
        return False

    # 2. Extract only alphabetic characters (ignore numbers, punctuation, spaces)
    alpha_chars = [char for char in text if char.isalpha()]

    # 3. Avoid division by zero if there are no letters at all
    if not alpha_chars:
        return False

    # 4. Count uppercase letters
    uppercase_count = sum(1 for char in alpha_chars if char.isupper())

    # 5. Calculate percentage of uppercase alphabetic characters
    uppercase_ratio = uppercase_count / len(alpha_chars)

    # 6. Return True if > 60% are uppercase
    return uppercase_ratio > 0.60

def check_repetitive_characters(text: str) -> bool:
    """Dimension 2b. True if any character repeats 4+ times consecutively."""
    pattern = re.compile(r"(.)\1{3,}")
    return bool(pattern.search(text))



def check_technical_breadcrumbs(text: str) -> bool:
    """Dimension 3. True if text contains at least ONE technical breadcrumb."""
    # 1. Matches common ID patterns (e.g. txn_12345, ch_abc123, inv_990, order #4401)
    id_pattern = r"\b(txn_|ch_|inv_)[a-zA-Z0-9_]+|\border\s*#\s*\d+\b"

    # 2. Matches common 3-digit HTTP status codes
    status_code_pattern = r"\b(400|401|403|404|500|502|503|504)\b"

    # 3. API endpoint paths (must start with / followed by a known route word or multi-segment path)
    api_path_pattern = r"(?<![a-zA-Z0-9_])/(?:[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+|api|v1|v2|v3|webhooks|charges|payments|checkout)\b"

    combined_pattern = re.compile(
        f"{id_pattern}|{status_code_pattern}|{api_path_pattern}",
        re.IGNORECASE,
    )

    return bool(combined_pattern.search(text))


def check_completeness(text: str, merchant_tier: str) -> list[str]:
    """Dimension 4. Evaluates character length thresholds against tier SLAs."""
    flags: list[str] = []

    # 1. Flag tickets with under 40 characters across all tiers
    if len(text) < 40:
        flags.append("INSUFFICIENT_DETAIL")

    # 2. Flag Enterprise tickets with under 80 characters (higher SLA bar)
    if merchant_tier == "Enterprise" and len(text) < 80:
        flags.append("ENTERPRISE_DETAIL_BELOW_SLA")

    return flags

def calculate_quality_score(
    issue_description: str, merchant_tier: str
) -> QualityReport:
    """Orchestrates all quality dimensions starting from 100 and applies deductions.

    Returns a dict with QualityReport fields plus the sanitized text:
    {
        "score": int,
        "status": str,
        "flags": list[str],
        "cleaned_text": str
    }
    """
    score = 100
    flags: list[str] = []

    # 1. Clean HTML / Markup
    has_html, text_after_html = check_html_and_markup(issue_description)
    if has_html:
        score -= 15
        flags.append("CONTAINS_HTML_OR_MARKUP")

    # 2. Normalize Whitespace
    was_excessive, cleaned_text = normalize_whitespace(text_after_html)
    if was_excessive:
        score -= 5
        flags.append("EXCESSIVE_WHITESPACE")

    # 3. Check Shouting
    if check_shouting(cleaned_text):
        score -= 15
        flags.append("EXCESSIVE_CAPITALIZATION")

    # 4. Check Repetitive Characters
    if check_repetitive_characters(cleaned_text):
        score -= 10
        flags.append("REPETITIVE_CHARACTERS")

    # 5. Check Technical Breadcrumbs
    if not check_technical_breadcrumbs(cleaned_text):
        score -= 30
        flags.append("MISSING_TECHNICAL_IDENTIFIERS")

    # 6. Check Completeness
    completeness_flags = check_completeness(cleaned_text, merchant_tier)
    for flag in completeness_flags:
        if flag == "INSUFFICIENT_DETAIL":
            score -= 25
        elif flag == "ENTERPRISE_DETAIL_BELOW_SLA":
            score -= 10
        flags.append(flag)

    # Clamp floor score at 0
    score = max(0, score)

    # Determine Quality Status
    if score >= 80:
        status = "EXCELLENT"
    elif score >= 50:
        status = "ACCEPTABLE"
    else:
        status = "REJECTED"

    return {
        "score": score,
        "status": status,
        "flags": flags,
        "cleaned_text": cleaned_text,
    }