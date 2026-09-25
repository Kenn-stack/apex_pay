from app.services.quality import (
    calculate_quality_score,
    check_completeness,
    check_html_and_markup,
    check_repetitive_characters,
    check_shouting,
    check_technical_breadcrumbs,
    normalize_whitespace,
)

# --------------------------------------------------------
# 1. Dimension 1: HTML & Whitespace
# --------------------------------------------------------

def test_check_html_and_markup_with_tags():
    raw = "<p>Payment failed with <b>504 error</b></p>"
    found, cleaned = check_html_and_markup(raw)
    assert found is True
    assert cleaned == "Payment failed with 504 error"


def test_normalize_whitespace_excessive():
    raw = "Payment   failed    with \n\n error 504  "
    was_excessive, cleaned = normalize_whitespace(raw)
    assert was_excessive is True
    assert cleaned == "Payment failed with error 504"


# --------------------------------------------------------
# 2. Dimension 2: Tone & Syntax
# --------------------------------------------------------

def test_check_shouting_true():
    text = "THE PAYMENT GATEWAY IS DOWN AND FAILING RIGHT NOW!"
    assert check_shouting(text) is True


def test_check_repetitive_characters_true():
    assert check_repetitive_characters("heeeeelp my system is down") is True


# --------------------------------------------------------
# 3. Dimension 3: Technical Breadcrumbs
# --------------------------------------------------------

def test_check_technical_breadcrumbs_valid():
    assert check_technical_breadcrumbs("Failed transaction txn_981234a") is True
    assert check_technical_breadcrumbs("Seeing a 504 timeout error") is True


def test_check_technical_breadcrumbs_false_positive_slash():
    text = "I tried logging in and out/back in again and it still fails"
    assert check_technical_breadcrumbs(text) is False


# --------------------------------------------------------
# 4. Dimension 4: Completeness
# --------------------------------------------------------

def test_check_completeness_enterprise_below_sla():
    text = "Webhook endpoint /webhooks/v1 is intermittently failing today."
    flags = check_completeness(text, "Enterprise")
    assert flags == ["ENTERPRISE_DETAIL_BELOW_SLA"]


# --------------------------------------------------------
# 5. Orchestrator: Score & Flag Assertions
# --------------------------------------------------------

def test_calculate_quality_score_excellent():
    description = (
        "We are receiving 504 Gateway Timeouts when sending POST requests "
        "to the /v1/charges endpoint for transaction txn_883912. Please investigate."
    )
    result = calculate_quality_score(description, "Starter")

    assert result["score"] == 100
    assert result["status"] == "EXCELLENT"
    assert result["flags"] == []


def test_calculate_quality_score_deductions_and_rejection():
    # Calculation:
    # 100 base
    # - 15 (CONTAINS_HTML_OR_MARKUP)
    # - 30 (MISSING_TECHNICAL_IDENTIFIERS)
    # - 25 (INSUFFICIENT_DETAIL)
    # Expected final score: 30 -> REJECTED
    description = "<p>Fix this broken checkout page right now</p>"
    result = calculate_quality_score(description, "Starter")

    assert result["score"] == 30
    assert result["status"] == "REJECTED"
    assert "CONTAINS_HTML_OR_MARKUP" in result["flags"]
    assert "MISSING_TECHNICAL_IDENTIFIERS" in result["flags"]
    assert "INSUFFICIENT_DETAIL" in result["flags"]
    assert result["cleaned_text"] == "Fix this broken checkout page right now"


def test_calculate_quality_score_floor_at_zero():
    # Cleaned length = 34 chars (31-39 range triggers both Shouting and Insufficient Detail).
    #
    # Deductions:
    # - 15 (CONTAINS_HTML_OR_MARKUP)
    # - 5  (EXCESSIVE_WHITESPACE)
    # - 15 (EXCESSIVE_CAPITALIZATION)
    # - 10 (REPETITIVE_CHARACTERS)
    # - 30 (NO_TECHNICAL_BREADCRUMBS)
    # - 25 (INSUFFICIENT_DETAIL)
    # Total = -100 -> Clamped at 0
    description = "<p>HEEEELP  FIX THIS SYSTEM NOW PLEASE</p>"
    result = calculate_quality_score(description, "Starter")

    assert result["score"] == 0
    assert result["status"] == "REJECTED"
    assert "CONTAINS_HTML_OR_MARKUP" in result["flags"]
    assert "EXCESSIVE_WHITESPACE" in result["flags"]
    assert "EXCESSIVE_CAPITALIZATION" in result["flags"]
    assert "REPETITIVE_CHARACTERS" in result["flags"]
    assert "MISSING_TECHNICAL_IDENTIFIERS" in result["flags"]
    assert "INSUFFICIENT_DETAIL" in result["flags"]