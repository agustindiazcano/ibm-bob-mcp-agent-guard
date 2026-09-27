"""Reference tests for ledger.statement -- eval fixture E3's ceiling suite.
See test_account_complete.py for how these are used."""
from ledger.statement import categorize, format_line, summarize


def test_categorize_credit():
    assert categorize(10.0) == "credit"


def test_categorize_debit():
    assert categorize(-5.0) == "debit"


def test_categorize_zero():
    assert categorize(0.0) == "zero"


def test_format_line_negative_amount():
    assert format_line("Coffee", -4.5, 95.5) == "Coffee: -$4.50 (balance: $95.50)"


def test_format_line_positive_amount():
    assert format_line("Paycheck", 1000.0, 1095.5) == "Paycheck: +$1000.00 (balance: $1095.50)"


def test_summarize_mixed_transactions():
    assert summarize([100, -30, -20, 50]) == {"credits": 150, "debits": -50, "net": 100}


def test_summarize_empty():
    assert summarize([]) == {"credits": 0, "debits": 0, "net": 0}
