# -*- coding: utf-8 -*-
"""
Unit tests for AI Event Planner core functions.
Covers:
- Currency conversion and number formatting
- 100-point priority budget calculations and validation
- Priority Shield deficit absorption and 0-point exclusion
- Vendor quote parser (line items, taxes, hidden flags, missing items)
"""

import pytest
import streamlit as st
from app import (
    points_to_amount,
    fmt_amount,
    currency_symbol,
    apply_priority_shield,
    parse_vendor_quote,
    CATEGORIES,
    EVENT_TYPES,
)


# =============================================================================
# 1. CURRENCY & FORMATTING TESTS
# =============================================================================
def test_points_to_amount():
    """Verify points accurately translate to exact financial amounts."""
    total = 500000.0
    assert points_to_amount(35, total) == 175000.0
    assert points_to_amount(25, total) == 125000.0
    assert points_to_amount(15, total) == 75000.0
    assert points_to_amount(0, total) == 0.0
    assert points_to_amount(100, total) == 500000.0


def test_fmt_amount_inr():
    """Verify Indian numbering format (Lakhs / Thousands separator)."""
    # Simulate INR session state
    st.session_state["currency"] = "INR"
    assert "₹" in fmt_amount(1000)
    assert fmt_amount(100000) == "₹1,00,000"
    assert fmt_amount(5000000) == "₹50,00,000"
    assert fmt_amount(500) == "₹500"


def test_fmt_amount_usd():
    """Verify standard USD comma formatting."""
    st.session_state["currency"] = "USD"
    assert fmt_amount(1000) == "$1,000"
    assert fmt_amount(100000) == "$100,000"
    assert fmt_amount(25.5) == "$26"  # Rounded to whole dollar


def test_currency_symbol():
    """Verify currency symbol switching."""
    st.session_state["currency"] = "INR"
    assert currency_symbol() == "₹"
    st.session_state["currency"] = "USD"
    assert currency_symbol() == "$"


# =============================================================================
# 2. PRIORITY SCORE VALIDATION (100-POINT SUM)
# =============================================================================
def test_priority_points_sum_to_100():
    """Verify default and valid custom allocations equal 100 points."""
    # Default distribution
    default_points = {"food": 35, "photo": 25, "venue": 25, "deco": 15}
    assert sum(default_points.values()) == 100

    # Custom distribution with 0-point category
    custom_points = {"food": 50, "photo": 30, "venue": 20, "deco": 0}
    assert sum(custom_points.values()) == 100

    # Invalid distribution detection
    invalid_points = {"food": 40, "photo": 30, "venue": 20, "deco": 0}
    assert sum(invalid_points.values()) != 100


def test_all_categories_present():
    """Verify all 4 core categories exist."""
    expected_categories = {"food", "photo", "venue", "deco"}
    assert set(CATEGORIES.keys()) == expected_categories


# =============================================================================
# 3. PRIORITY SHIELD ALGORITHM TESTS
# =============================================================================
def test_priority_shield_protection_and_cut():
    """
    Verify top priority categories remain protected, while lower categories
    absorb the budget deficit.
    """
    total_budget = 100000.0
    drop_pct = 20  # 20% cut -> deficit = 20,000
    points = {"food": 35, "photo": 25, "venue": 25, "deco": 15}

    result = apply_priority_shield(points, drop_pct, total_budget)

    # Budget checks
    assert result["new_budget"] == 80000.0
    assert sum(result["new_allocs"].values()) == 80000.0

    # Top 2 protected
    assert "food" in result["protected_cats"]
    assert "photo" in result["protected_cats"] or "venue" in result["protected_cats"]
    assert result["new_allocs"]["food"] == 35000.0  # 100% protected

    # Low priority compressed
    assert result["new_allocs"]["deco"] < result["original_allocs"]["deco"]
    assert result["remaining_deficit"] == 0.0


def test_priority_shield_excludes_zero_point_categories():
    """
    Verify categories with 0 points are excluded from cuts and do not trigger
    false deficit warnings.
    """
    total_budget = 100000.0
    drop_pct = 20  # deficit = 20,000
    points = {"food": 50, "photo": 50, "venue": 0, "deco": 0}

    result = apply_priority_shield(points, drop_pct, total_budget)

    # Zero categories must remain 0
    assert result["new_allocs"]["venue"] == 0.0
    assert result["new_allocs"]["deco"] == 0.0
    assert "venue" in result["zero_cats"]
    assert "deco" in result["zero_cats"]

    # Active funded categories absorb the cut
    assert result["new_allocs"]["food"] == 50000.0  # #1 priority protected
    assert result["new_allocs"]["photo"] == 30000.0  # absorbed 20,000 deficit
    assert result["remaining_deficit"] == 0.0  # No false deficit alarm


# =============================================================================
# 4. VENDOR QUOTE PARSER TESTS
# =============================================================================
def test_parse_vendor_quote_line_items_and_tax():
    """Test extracting line items and separate GST/tax lines."""
    mock_quote = """
    Grand Ballroom Venue Rental: ₹50,000
    Buffet Catering (100 pax): ₹75,000
    Candid Photography & Video: ₹30,000
    GST (18%): ₹27,900
    Grand Total: ₹1,82,900
    """
    parsed = parse_vendor_quote(mock_quote, event_type="Wedding")

    assert len(parsed["items"]) >= 3
    names = [i["name"].lower() for i in parsed["items"]]
    assert any("venue" in n for n in names)
    assert any("catering" in n for n in names)
    assert any("photography" in n for n in names)

    # Subtotal check (excludes tax and grand total)
    assert parsed["subtotal"] == 155000.0


def test_parse_vendor_quote_missing_items():
    """Test missing item flags for an event type."""
    minimal_quote = """
    Buffet Lunch: ₹20,000
    Sound System: ₹5,000
    """
    parsed = parse_vendor_quote(minimal_quote, event_type="Birthday")

    # Cake and Photography are expected for Birthday and missing in the quote
    missing = [m.lower() for m in parsed["missing_items"]]
    assert "cake" in missing
    assert "photography" in missing


def test_parse_vendor_quote_hidden_flags():
    """Test detection of common unmentioned hidden charges."""
    quote = "Basic Hall Rental - ₹40,000"
    parsed = parse_vendor_quote(quote, event_type="Wedding")

    # Should flag missing overtime, cleanup, etc.
    assert len(parsed["hidden_flags"]) > 0
    flags_text = " ".join(parsed["hidden_flags"]).lower()
    assert "overtime" in flags_text or "cleanup" in flags_text
