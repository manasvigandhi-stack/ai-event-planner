# -*- coding: utf-8 -*-
"""
AI EVENT PLANNER — Build with AI Challenge 5 (Google for Developers)

A Streamlit application that guides users through 4 interactive steps to
plan their perfect event using Google Gemini AI.

Steps:
    1. Vibe Calibration & Negative Constraints
    2. 100-Point Priority Budget Engine
    3. What-If Budget Drop Simulator & Priority Shield
    4. Smart Timeline & Vendor Quote Parser
"""

import html
import logging
import os
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
import plotly.graph_objects as go

# ── Optional: Load .env for local development ─────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
    _ENV_KEY = os.getenv("GEMINI_API_KEY", "")
except ImportError:
    _ENV_KEY = ""

# ── Optional: Google Generative AI ───────────────────────────────────────────
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="AI Event Planner ✨",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS — Modern, polished UI
# =============================================================================
CUSTOM_CSS = """
<style>
/* ── Global ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Step header banner ── */
.step-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 1.2rem 1.6rem;
    color: white;
    margin-bottom: 1.4rem;
    box-shadow: 0 4px 20px rgba(102,126,234,0.35);
}
.step-banner h2 { margin: 0; font-size: 1.45rem; font-weight: 700; }
.step-banner p  { margin: 0.25rem 0 0; opacity: 0.88; font-size: 0.92rem; }

/* ── Vibe summary card ── */
.vibe-card {
    background: linear-gradient(135deg, #f8f7ff 0%, #ede9fe 100%);
    border-left: 5px solid #7c3aed;
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 12px rgba(124,58,237,0.12);
}
.vibe-card h4 { color: #5b21b6; margin-top: 0; margin-bottom: 0.5rem; font-size: 1rem; }
.vibe-card p  { margin: 0; line-height: 1.65; color: #374151; font-size: 0.97rem; }

/* ── DIY recommendation card ── */
.diy-card {
    border-left: 4px solid #6366f1;
    background: linear-gradient(135deg, #fafafa 0%, #f0f4ff 100%);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0;
    box-shadow: 0 2px 8px rgba(99,102,241,0.10);
}
.diy-card h5 { color: #4338ca; margin: 0 0 0.4rem; font-size: 0.92rem; }
.diy-card ul { margin: 0; padding-left: 1.2rem; }
.diy-card li { color: #374151; font-size: 0.92rem; line-height: 1.6; }

/* ── Shield / compression badges ── */
.badge-shield {
    display: inline-block;
    background: #10b981;
    color: white;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-left: 6px;
    vertical-align: middle;
}
.badge-compressed {
    display: inline-block;
    background: #f59e0b;
    color: white;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-left: 6px;
    vertical-align: middle;
}

/* ── Vendor quote table ── */
.vendor-table { width: 100%; border-collapse: collapse; font-size: 0.93rem; }
.vendor-table th {
    background: #6366f1; color: white;
    padding: 8px 12px; text-align: left;
}
.vendor-table td { padding: 7px 12px; border-bottom: 1px solid #e5e7eb; }
.vendor-table tr:hover td { background: #f5f3ff; }
.vendor-table .tax-row td { background: #fff7ed; color: #92400e; font-weight: 500; }
.vendor-table .warn-row td { background: #fef2f2; color: #991b1b; }

/* ── Progress timeline ── */
.task-overdue   { color: #dc2626; font-weight: 600; }
.task-urgent    { color: #d97706; font-weight: 500; }
.task-ontrack   { color: #059669; }
.task-done      { color: #4b5563; text-decoration: line-through; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #f8f7ff;
    border-radius: 12px;
    padding: 0.8rem;
    border: 1px solid #ede9fe;
}

/* ── Section dividers ── */
.section-divider {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #667eea, transparent);
    margin: 1.5rem 0;
}

/* ── Highlight box ── */
.info-box {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    margin: 0.8rem 0;
    font-size: 0.93rem;
    color: #1e40af;
}

/* ── Sidebar styling ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
}
[data-testid="stSidebar"] * { color: #e0e7ff !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: #c7d2fe !important; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================
EVENT_TYPES = ["Wedding", "Birthday", "Community Gathering", "Anniversary", "Other"]

STYLE_TAGS = [
    "Traditional", "Intimate", "Modern Minimalist", "Bohemian", "Grand",
    "Rustic", "Garden / Outdoor", "Fairytale", "Classic Elegant", "Festive & Vibrant",
]

CATEGORIES = {
    "food":  {"label": "🍽️ Food & Catering",        "color": "#6366f1"},
    "photo": {"label": "📸 Photography & Video",      "color": "#ec4899"},
    "venue": {"label": "🏛️ Venue & Rentals",         "color": "#f59e0b"},
    "deco":  {"label": "🌸 Decoration & Lighting",    "color": "#10b981"},
}

# Module-level compiled regex patterns for vendor quote parsing efficiency
ITEM_PATTERN = re.compile(
    r"^(.+?)\s*[-:]\s*[₹$₨Rs\.]?\s*([\d,]+(?:\.\d{1,2})?)",
    re.MULTILINE | re.IGNORECASE,
)
GST_PATTERN = re.compile(
    r"(?:GST|CGST|SGST|IGST|Service\s+(?:Charge|Tax)|VAT|Tax)[^\n]*",
    re.IGNORECASE,
)
TAX_PATTERN = re.compile(
    r"GST|CGST|SGST|IGST|service\s+charge|VAT|tax",
    re.IGNORECASE,
)
TOTAL_PATTERN = re.compile(
    r"\btotal\b|\bgrand\s+total\b|\bnet\b",
    re.IGNORECASE,
)

# Task templates keyed by event type (days_before = days before the event)
TASK_TEMPLATES = {
    "Wedding": [
        {"days_before": 365, "task": "Set event date & rough guest count",      "category": "Planning",     "depends_on": []},
        {"days_before": 270, "task": "Visit & book venue",                       "category": "Venue",        "depends_on": ["Set event date & rough guest count"]},
        {"days_before": 240, "task": "Book caterer & finalize cuisine style",    "category": "Catering",     "depends_on": ["Visit & book venue"]},
        {"days_before": 210, "task": "Book photographer & videographer",         "category": "Photography",  "depends_on": []},
        {"days_before": 180, "task": "Send save-the-dates",                      "category": "Invitations",  "depends_on": ["Set event date & rough guest count"]},
        {"days_before": 150, "task": "Order bridal attire & groom outfit",       "category": "Attire",       "depends_on": []},
        {"days_before": 120, "task": "Book florist & decoration vendor",         "category": "Decoration",   "depends_on": ["Visit & book venue"]},
        {"days_before":  90, "task": "Send formal invitations",                  "category": "Invitations",  "depends_on": ["Send save-the-dates"]},
        {"days_before":  60, "task": "Book hair & make-up artists",              "category": "Beauty",       "depends_on": []},
        {"days_before":  45, "task": "Arrange guest accommodation & transport",  "category": "Logistics",    "depends_on": ["Send formal invitations"]},
        {"days_before":  30, "task": "Confirm guest count with caterer",         "category": "Catering",     "depends_on": ["Send formal invitations"]},
        {"days_before":  21, "task": "Final fitting & attire pickup",            "category": "Attire",       "depends_on": ["Order bridal attire & groom outfit"]},
        {"days_before":  14, "task": "Final venue walkthrough with vendors",     "category": "Venue",        "depends_on": ["Visit & book venue"]},
        {"days_before":   7, "task": "Prepare final vendor payments",            "category": "Finance",      "depends_on": []},
        {"days_before":   3, "task": "Confirm all vendor arrival times",         "category": "Logistics",    "depends_on": []},
        {"days_before":   1, "task": "Venue setup & decoration",                 "category": "Decoration",   "depends_on": ["Book florist & decoration vendor"]},
        {"days_before":   0, "task": "Event Day — Enjoy! 🎉",                   "category": "Event",        "depends_on": []},
    ],
    "Birthday": [
        {"days_before":  90, "task": "Set date, theme & rough guest count",     "category": "Planning",    "depends_on": []},
        {"days_before":  60, "task": "Book venue or arrange home setup",         "category": "Venue",       "depends_on": ["Set date, theme & rough guest count"]},
        {"days_before":  45, "task": "Book caterer / order cake",                "category": "Catering",    "depends_on": []},
        {"days_before":  40, "task": "Book photographer",                        "category": "Photography", "depends_on": []},
        {"days_before":  30, "task": "Send invitations",                         "category": "Invitations", "depends_on": ["Set date, theme & rough guest count"]},
        {"days_before":  21, "task": "Order decorations & supplies",             "category": "Decoration",  "depends_on": ["Book venue or arrange home setup"]},
        {"days_before":  14, "task": "Confirm RSVPs & finalize headcount",       "category": "Invitations", "depends_on": ["Send invitations"]},
        {"days_before":   7, "task": "Prepare party favours & return gifts",     "category": "Extras",      "depends_on": []},
        {"days_before":   3, "task": "Confirm vendor arrival times",             "category": "Logistics",   "depends_on": []},
        {"days_before":   1, "task": "Venue / home decoration setup",            "category": "Decoration",  "depends_on": ["Order decorations & supplies"]},
        {"days_before":   0, "task": "Party Time! 🎂",                          "category": "Event",       "depends_on": []},
    ],
    "Anniversary": [
        {"days_before": 120, "task": "Decide on celebration style & scale",      "category": "Planning",    "depends_on": []},
        {"days_before":  90, "task": "Book venue or plan private dinner",         "category": "Venue",       "depends_on": ["Decide on celebration style & scale"]},
        {"days_before":  60, "task": "Book photographer for candid shoot",        "category": "Photography", "depends_on": []},
        {"days_before":  45, "task": "Plan menu & book caterer / restaurant",     "category": "Catering",    "depends_on": []},
        {"days_before":  30, "task": "Send invitations (if group celebration)",   "category": "Invitations", "depends_on": []},
        {"days_before":  21, "task": "Arrange floral décor & ambience details",   "category": "Decoration",  "depends_on": ["Book venue or plan private dinner"]},
        {"days_before":  14, "task": "Plan surprise elements / entertainment",    "category": "Extras",      "depends_on": []},
        {"days_before":   7, "task": "Confirm guest count & finalize menu",       "category": "Catering",    "depends_on": []},
        {"days_before":   3, "task": "Confirm all vendor timings",                "category": "Logistics",   "depends_on": []},
        {"days_before":   1, "task": "Setup & final decoration",                  "category": "Decoration",  "depends_on": []},
        {"days_before":   0, "task": "Celebrate Love! 💍",                       "category": "Event",       "depends_on": []},
    ],
    "Community Gathering": [
        {"days_before": 120, "task": "Define purpose, theme & expected attendance","category": "Planning",   "depends_on": []},
        {"days_before":  90, "task": "Reserve community hall / open ground",       "category": "Venue",      "depends_on": ["Define purpose, theme & expected attendance"]},
        {"days_before":  75, "task": "Confirm volunteers & organizing committee",  "category": "Logistics",  "depends_on": []},
        {"days_before":  60, "task": "Arrange catering / food stalls",             "category": "Catering",   "depends_on": []},
        {"days_before":  45, "task": "Announce event & send community invites",    "category": "Invitations","depends_on": ["Reserve community hall / open ground"]},
        {"days_before":  30, "task": "Book stage, sound & AV equipment",           "category": "AV & Stage", "depends_on": ["Reserve community hall / open ground"]},
        {"days_before":  21, "task": "Arrange decoration & banners",               "category": "Decoration", "depends_on": []},
        {"days_before":  14, "task": "Finalize program / schedule",                "category": "Planning",   "depends_on": []},
        {"days_before":   7, "task": "Confirm headcount & logistics",              "category": "Logistics",  "depends_on": []},
        {"days_before":   3, "task": "Prepare volunteer briefing & task list",     "category": "Logistics",  "depends_on": []},
        {"days_before":   1, "task": "Venue setup, stage & decoration",            "category": "Decoration", "depends_on": []},
        {"days_before":   0, "task": "Community Day — Celebrate Together! 🤝",    "category": "Event",      "depends_on": []},
    ],
}

# DIY fallback templates per category (used when Gemini API key is absent)
DIY_TEMPLATES = {
    "food": [
        "Partner with local home caterers or tiffin services for authentic, affordable menus.",
        "Consider a curated grazing table with seasonal fruits, local sweets & charcuterie — chic yet budget-friendly.",
        "Set up a DIY chaat / dessert station — guests love interactive food experiences.",
    ],
    "photo": [
        "Hire a talented photography student from a local art college — fresh talent, authentic shots.",
        "Create a beautiful DIY photo booth with fairy lights, printed props & a shared Google Photos album.",
        "Ask 2–3 guests to be designated 'memory keepers' with good phone cameras for candid shots.",
    ],
    "venue": [
        "A private farmhouse or heritage bungalow rental is often cheaper than banquet halls & far more unique.",
        "Outdoor gardens, parks, or rooftop terraces with good lighting can look stunning on a budget.",
        "Collaborate with a local café or restaurant for a buy-out evening — great value, built-in kitchen.",
    ],
    "deco": [
        "Use potted plants & marigold strings instead of cut flowers — lasts longer & costs ¼ of the price.",
        "Thrifted candle holders, fairy lights & fabric draping create magic without the vendor markup.",
        "Visit a local wholesale flower market at dawn for fresh blooms at 30–40% of retail price.",
    ],
}

# Sample quote for demo
SAMPLE_VENDOR_QUOTE = """WEDDING CATERING QUOTE — Saffron Hospitality
Date: 15 March 2025 | Guests: 300

Buffet Catering (Veg + Non-Veg): 150,000
Welcome Drinks & Mocktails: 18,000
Live Counters (3 nos): 24,000
Dessert Station: 12,000
Service Staff (15 pax): 22,500
Cutlery & Crockery Rental: 8,000
CGST @ 9%: 21,105
SGST @ 9%: 21,105

Subtotal (before tax): 234,500
Total: 276,710

Note: Above quote does not include generator rental, post-event cleanup, or overtime beyond 11 PM.
"""


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
def init_session_state() -> None:
    """Initialize all session state variables with default values."""
    defaults = {
        # App navigation
        "step": 1,
        "nav_page": "1. Vibe Calibration",
        "nav_selection": "1. Vibe Calibration",
        "currency": "INR",

        # Step 1 — Vibe Calibration
        "event_type": "Wedding",
        "custom_event_type": "",
        "style_tags": [],
        "hard_nos": "",
        "vibe_confirmed": False,
        "vibe_summary": "",

        # Step 2 — Budget Engine
        "total_budget": 500000.0,
        "points_food": 35,
        "points_photo": 25,
        "points_venue": 25,
        "points_deco": 15,
        "budget_locked": False,

        # Step 3 — What-If Simulator
        "has_budget_drop": False,
        "drop_pct": 20,
        "shield_result": None,
        "diy_cards": {},

        # Step 4 — Timeline
        "event_date": date.today() + timedelta(days=180),
        "last_timeline_event_type": "Wedding",
        "task_done": {},

        # Step 4B — Vendor Parser
        "vendor_quote_text": "",
        "vendor_parse_result": None,

        # Gemini
        "gemini_key": _ENV_KEY,
        "gemini_model": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def set_nav_page(page_name: str) -> None:
    """Update navigation selection across state keys and trigger immediate rerun."""
    st.session_state["nav_page"] = page_name
    st.session_state["nav_selection"] = page_name
    st.rerun()


# =============================================================================
# GEMINI HELPER
# =============================================================================
@st.cache_resource
def get_cached_gemini_model(api_key: str) -> Any:
    """Load and cache the Gemini GenerativeModel instance for a given API key."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def get_gemini_model() -> Any:
    """Return a configured Gemini model instance, or None if unavailable."""
    if not _GENAI_AVAILABLE:
        return None
    key = st.session_state.get("gemini_key", "").strip()
    if not key:
        return None
    try:
        return get_cached_gemini_model(key)
    except Exception as exc:
        logging.debug("Fallback triggered: %s", exc)
        return None


def gemini_generate_rest(prompt: str, api_key: str) -> str:
    """Call Gemini REST API directly using standard requests library."""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=12)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def gemini_generate(prompt: str, fallback: str) -> str:
    """
    Call Gemini with the given prompt.
    1. Tries google.generativeai SDK first if available.
    2. Falls back to direct Gemini REST API call.
    3. Falls back gracefully to smart custom template text if key is absent or on network errors.
    """
    key = st.session_state.get("gemini_key", "").strip()
    if not key:
        return fallback

    # Try SDK first
    if _GENAI_AVAILABLE:
        try:
            model = get_gemini_model()
            if model is not None:
                response = model.generate_content(prompt)
                if response and hasattr(response, "text") and response.text:
                    return response.text.strip()
        except Exception as exc:
            logging.debug("Fallback triggered: %s", exc)

    # Try direct REST API fallback
    try:
        return gemini_generate_rest(prompt, key)
    except Exception as exc:
        logging.debug("Fallback triggered: %s", exc)
        return fallback


# =============================================================================
# UTILITY HELPERS
# =============================================================================
def currency_symbol(currency: Optional[str] = None) -> str:
    """Return the currency symbol ('₹' or '$') for the active or provided currency."""
    curr = currency or (st.session_state.get("currency", "INR") if "currency" in st.session_state else "INR")
    return "₹" if curr == "INR" else "$"


def fmt_amount(amount: float, currency: Optional[str] = None) -> str:
    """Format a numeric amount into a localized currency string."""
    sym = currency_symbol(currency)
    curr = currency or (st.session_state.get("currency", "INR") if "currency" in st.session_state else "INR")
    if curr == "INR":
        # Indian number formatting: 1,00,000
        amount_int = int(round(amount))
        s = str(amount_int)
        if len(s) <= 3:
            return f"{sym}{s}"
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)
        formatted = ",".join(reversed(parts)) + "," + last3
        return f"{sym}{formatted}"
    else:
        return f"{sym}{amount:,.0f}"


def points_to_amount(points: int, total: float) -> float:
    """Calculate budget amount allocated based on point score."""
    return (points / 100) * total


def get_points_dict() -> Dict[str, int]:
    """Return dictionary mapping core category keys to their assigned points."""
    return {k: int(st.session_state.get(f"points_{k}", 0)) for k in CATEGORIES}


def total_points() -> int:
    """Calculate total points allocated across all active categories."""
    return sum(get_points_dict().values())


# =============================================================================
# PRIORITY SHIELD ALGORITHM
# =============================================================================
@st.cache_data
def apply_priority_shield(points: dict, drop_pct: int, total_budget: float) -> dict:
    """
    Applies the Priority Shield algorithm:
    - Categories with 0 points / ₹0 allocations are automatically excluded from absorbing cuts.
    - Top 2 highest-priority categories are PROTECTED.
    - Deficit is distributed PROPORTIONALLY across all compressible categories
      (categories outside the top 2 protected list that have points > 0).
    - Safety floor: ensures no compressible category drops below 30% of its original budget.
    - If deficit cannot be fully absorbed due to the safety floor, remaining deficit is flagged.
    
    Returns:
        dict with keys: new_budget, original_allocs, new_allocs,
                        protected_cats, vulnerable_cats, compressible_cats, zero_cats, remaining_deficit
    """
    new_budget = total_budget * (1 - drop_pct / 100)
    deficit = total_budget - new_budget

    original_allocs = {cat: points_to_amount(pts, total_budget) for cat, pts in points.items()}
    new_allocs = dict(original_allocs)

    # Active categories with points > 0 sorted descending
    sorted_active = [cat for cat, pts in sorted(points.items(), key=lambda x: x[1], reverse=True) if pts > 0]
    zero_cats = [cat for cat, pts in points.items() if pts == 0]

    if len(sorted_active) >= 3:
        protected_cats = sorted_active[:2]
        compressible_cats = sorted_active[2:]
    elif len(sorted_active) == 2:
        protected_cats = [sorted_active[0]]
        compressible_cats = [sorted_active[1]]
    elif len(sorted_active) == 1:
        protected_cats = [sorted_active[0]]
        compressible_cats = []
    else:
        protected_cats = []
        compressible_cats = []

    total_compressible_orig = sum(original_allocs[cat] for cat in compressible_cats)

    if total_compressible_orig > 0 and deficit > 0:
        # Max reduction allowed per category is 70% of its original budget (retaining 30% safety floor)
        max_possible_cut = 0.70 * total_compressible_orig
        if deficit <= max_possible_cut:
            # Proportional cut across all compressible categories
            allocated_cut = 0.0
            for i, cat in enumerate(compressible_cats):
                orig = original_allocs[cat]
                if i == len(compressible_cats) - 1:
                    cut = round(deficit - allocated_cut, 2)
                else:
                    cut = round(deficit * (orig / total_compressible_orig), 2)
                    allocated_cut += cut
                new_allocs[cat] = round(orig - cut, 2)
            remaining = 0.0
        else:
            # Safety floor enforced: cap compression at 70% cut (each retains exactly 30% floor)
            for cat in compressible_cats:
                orig = original_allocs[cat]
                max_cut = round(0.70 * orig, 2)
                new_allocs[cat] = round(orig - max_cut, 2)
            remaining = round(deficit - max_possible_cut, 2)
    else:
        remaining = deficit if (compressible_cats or not sorted_active) and deficit > 0 else 0.0

    return {
        "new_budget": new_budget,
        "original_allocs": original_allocs,
        "new_allocs": new_allocs,
        "protected_cats": protected_cats,
        "vulnerable_cats": compressible_cats,
        "compressible_cats": compressible_cats,
        "zero_cats": zero_cats,
        "remaining_deficit": max(0.0, round(remaining, 2)),
    }


# =============================================================================
# VENDOR QUOTE PARSER
# =============================================================================
@st.cache_data
def parse_vendor_quote(text: str, event_type: str) -> dict:
    """
    Regex-based vendor quote parser.
    Extracts line items, taxes, and flags potentially hidden/missing charges.
    """
    items = []
    tax_lines = []
    total = 0.0

    for match in ITEM_PATTERN.finditer(text):
        name = match.group(1).strip().rstrip("-:").strip()
        amt_str = match.group(2).replace(",", "")
        try:
            amt = float(amt_str)
        except ValueError:
            continue
        is_tax = bool(TAX_PATTERN.search(name))
        is_total = bool(TOTAL_PATTERN.search(name))
        items.append({"name": name, "amount": amt, "is_tax": is_tax, "is_total": is_total})
        if not is_total and not is_tax:
            total += amt

    # Standalone GST mentions without amounts
    for m in GST_PATTERN.finditer(text):
        line = m.group(0).strip()
        if not any(line in i["name"] for i in items):
            tax_lines.append(line)

    # Common expected items per event type
    expected = {
        "Wedding":            ["venue", "catering", "photography", "decoration", "music", "transport"],
        "Birthday":           ["venue", "catering", "cake", "decoration", "photography"],
        "Anniversary":        ["venue", "catering", "decoration", "photography"],
        "Community Gathering":["venue", "catering", "sound", "decoration", "transport"],
    }
    found_keywords = " ".join(i["name"].lower() for i in items)
    missing = []
    for keyword in expected.get(event_type, []):
        if keyword not in found_keywords:
            missing.append(keyword.capitalize())

    # Hidden-charge flags (keywords that often hide costs)
    hidden_flags = []
    hidden_kw = [
        ("overtime", "Overtime charges may apply if the event runs long"),
        ("corkage", "Corkage / bring-your-own fees not included"),
        ("cleanup", "Post-event cleanup fee may not be included"),
        ("generator", "Generator / power backup cost may be extra"),
        ("parking", "Parking fees may be separately billed to guests"),
        ("service charge", "Service charge may have GST applied on top"),
    ]
    text_lower = text.lower()
    for kw, msg in hidden_kw:
        if kw not in text_lower:
            hidden_flags.append(f"⚠️ Watch out: {msg}")

    return {
        "items": items,
        "extra_tax_lines": tax_lines,
        "subtotal": total,
        "missing_items": missing,
        "hidden_flags": hidden_flags[:4],  # top 4 flags
    }


# =============================================================================
# PLOTLY HELPERS
# =============================================================================
@st.cache_data
def make_donut_chart(
    points: dict,
    total_budget: float,
    currency: str = "INR",
) -> go.Figure:
    """Generate an interactive Plotly donut chart representing budget distribution."""
    labels = [CATEGORIES[k]["label"] for k in points if k in CATEGORIES]
    amounts = [points_to_amount(points[k], total_budget) for k in points if k in CATEGORIES]
    colors = [CATEGORIES[k]["color"] for k in points if k in CATEGORIES]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=amounts,
        hole=0.52,
        marker=dict(colors=colors, line=dict(color="white", width=3)),
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(t=20, b=40, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4),
        showlegend=True,
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b>{fmt_amount(total_budget, currency=currency)}</b>",
            x=0.5, y=0.5, font_size=14, showarrow=False,
        )],
    )
    return fig


@st.cache_data
def make_comparison_bar(
    original_allocs: dict,
    new_allocs: dict,
    protected_cats: List[str],
    currency: str = "INR",
) -> go.Figure:
    """Generate a grouped bar chart comparing budget allocations before and after Priority Shield."""
    active_keys = [k for k in CATEGORIES if k in original_allocs and k in new_allocs]
    labels  = [CATEGORIES[k]["label"] for k in active_keys]
    orig    = [original_allocs[k] for k in active_keys]
    revised = [new_allocs[k] for k in active_keys]
    bar_colors_orig    = [CATEGORIES[k]["color"] for k in active_keys]
    bar_colors_revised = [
        "#10b981" if k in protected_cats and new_allocs[k] == original_allocs[k]
        else ("#4b5563" if original_allocs[k] == 0 else "#f59e0b")
        for k in active_keys
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Original Budget", x=labels, y=orig,
        marker_color=bar_colors_orig, opacity=0.55,
        text=[fmt_amount(v, currency=currency) for v in orig], textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="After Shield", x=labels, y=revised,
        marker_color=bar_colors_revised,
        text=[fmt_amount(v, currency=currency) for v in revised], textposition="outside",
    ))
    fig.update_layout(
        barmode="group",
        height=360,
        margin=dict(t=30, b=30, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(showticklabels=False, showgrid=False),
    )
    return fig


# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar() -> None:
    """Render the application sidebar with navigation, settings, and progress summary."""
    with st.sidebar:
        st.markdown("## 🎉 AI Event Planner")
        st.markdown("---")

        # Sidebar Navigation Radio Menu
        st.markdown("### 🧭 Navigation")
        nav_options = [
            "1. Vibe Calibration",
            "2. Budget Engine & Pie Chart",
            "3. Priority Shield Simulator",
            "4. Timeline & Quote Parser",
        ]
        
        current_nav = st.session_state.get("nav_page", nav_options[0])
        default_idx = nav_options.index(current_nav) if current_nav in nav_options else 0

        selected_page = st.radio(
            "Navigate",
            nav_options,
            index=default_idx,
        )
        st.session_state.nav_page = selected_page
        st.session_state.nav_selection = selected_page

        st.markdown("---")

        # Gemini API Key
        st.markdown("### 🔑 Gemini API Key")
        key_input = st.text_input(
            "Paste your key (optional)",
            value=st.session_state.gemini_key,
            type="password",
            help="Get a free key at aistudio.google.com — leave blank to use template fallbacks.",
            label_visibility="collapsed",
        )
        if key_input != st.session_state.gemini_key:
            st.session_state.gemini_key = key_input

        st.caption(
            "Optional: Enter your key for live AI-generated vibe customizations and quote parsing. "
            "Left blank, the app runs seamlessly on built-in smart templates."
        )

        if _GENAI_AVAILABLE and st.session_state.gemini_key:
            st.markdown("✅ *AI features active*")
        elif not _GENAI_AVAILABLE:
            st.markdown("⚠️ *google-generativeai not installed*")
        else:
            st.markdown("💡 *Using smart templates*")

        st.markdown("---")

        # Currency toggle
        st.markdown("### 💱 Currency")
        currency = st.radio(
            "Select currency",
            ["INR (₹)", "USD ($)"],
            index=0 if st.session_state.currency == "INR" else 1,
            label_visibility="collapsed",
        )
        st.session_state.currency = "INR" if "INR" in currency else "USD"

        st.markdown("---")

        # Status Overview
        st.markdown("### 📊 Status Overview")
        step4_active = bool(st.session_state.get("vendor_parse_result")) or any(
            st.session_state.get("task_done", {}).values()
        )
        steps = [
            ("1", "Vibe Calibration", st.session_state.vibe_confirmed),
            ("2", "Budget Engine",    st.session_state.budget_locked),
            ("3", "What-If Shield",   st.session_state.shield_result is not None),
            ("4", "Timeline & Vendor", step4_active),
        ]
        for num, label, done in steps:
            icon = "✅" if done else "⏳"
            st.markdown(f"{icon} **Step {num}**: {label}")

        st.markdown("---")

        if st.button("🔄 Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.75rem;opacity:0.6;text-align:center;'>"
            "Built with ❤️ using Streamlit & Gemini</div>",
            unsafe_allow_html=True,
        )


# =============================================================================
# STEP 1 — VIBE CALIBRATION
# =============================================================================
def render_step1() -> None:
    """Render Step 1: Vibe Calibration and aesthetic profile generation."""
    st.markdown("""
    <div class="step-banner" role="region" aria-label="Step 1: Vibe Calibration">
        <h2>✨ Step 1 — Vibe Calibration</h2>
        <p>Define your event's aesthetic DNA and tell us what to absolutely avoid.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### 🎊 Event Type")
        # Determine which option to pre-select in the dropdown
        _stored = st.session_state.event_type
        _sel_index = EVENT_TYPES.index(_stored) if _stored in EVENT_TYPES else EVENT_TYPES.index("Other")
        event_type = st.selectbox(
            "What kind of event are you planning?",
            EVENT_TYPES,
            index=_sel_index,
            label_visibility="collapsed",
        )
        if event_type == "Other":
            custom = st.text_input(
                "Specify your event type",
                value=st.session_state.custom_event_type,
                placeholder="e.g., Graduation Party, Housewarming…",
            )
            st.session_state.custom_event_type = custom
            if custom.strip():
                st.session_state.event_type = custom.strip()
            else:
                st.session_state.event_type = "Other"
        else:
            st.session_state.event_type = event_type
            st.session_state.custom_event_type = ""

        st.markdown("#### 🎨 Style Tags")
        st.caption("Select all that resonate with your vision")
        style_tags = st.multiselect(
            "Style Tags",
            STYLE_TAGS,
            default=st.session_state.style_tags,
            label_visibility="collapsed",
        )
        st.session_state.style_tags = style_tags

    with col2:
        st.markdown("#### 🚫 Hard Nos — Your Non-Negotiables")
        st.caption("Anything you absolutely don't want at your event")
        hard_nos = st.text_area(
            "Hard Nos",
            value=st.session_state.hard_nos,
            height=140,
            placeholder=(
                "e.g., No neon lights, no commercial banquet hall vibe, "
                "no loud DJ, no plastic chairs, no artificial flowers…"
            ),
            label_visibility="collapsed",
        )
        st.session_state.hard_nos = hard_nos

        st.markdown("")  # spacer
        if st.button("✨ Generate My Vibe Profile", use_container_width=True, type="primary"):
            if not style_tags:
                st.warning("Please select at least one style tag first.")
            else:
                with st.spinner("Crafting your personalized vibe profile…"):
                    prompt = f"""You are an expert event designer with 15 years of experience.
The client is planning a {event_type}.
Their style preferences: {", ".join(style_tags) if style_tags else "unspecified"}.
Their Hard Nos (things to absolutely avoid): {hard_nos if hard_nos else "none specified"}.

Write a vivid, warm, and encouraging "Reality Preview Summary" of exactly 3 sentences that:
1. Opens by confidently affirming you understand their unique vision.
2. Weaves in their style tags and respectfully acknowledges what they want to avoid.
3. Paints a brief, evocative picture of the overall mood and atmosphere they'll create.

Keep it under 85 words. Be specific, poetic, and uplifting — not generic."""
                    fallback = (
                        f"Your **{event_type}** vision is beautifully clear — "
                        f"a {', '.join(style_tags[:3]) if style_tags else 'unique'} celebration "
                        f"that is entirely, distinctly *you*. "
                        f"{'Steering clear of ' + hard_nos[:60] + '…, ' if hard_nos else ''}"
                        f"every detail will be curated to honour your aesthetic instincts. "
                        f"Get ready for an event that feels less like a production and more like a poem."
                    )
                    st.session_state.vibe_summary = gemini_generate(prompt, fallback)
                    st.session_state.vibe_confirmed = False  # reset lock if re-generated

    # Display the AI summary card
    if st.session_state.vibe_summary:
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        st.markdown("#### 🌟 Your AI Reality Preview")
        st.markdown(f"""
        <div class="vibe-card" role="region" aria-label="AI Reality Preview Profile">
            <h4>✨ Vibe Profile — {html.escape(str(st.session_state.event_type))}</h4>
            <p>{html.escape(str(st.session_state.vibe_summary))}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        col_a, col_b, _ = st.columns([1.4, 1.4, 1])
        with col_a:
            if st.button("🔁 Regenerate", use_container_width=True):
                st.session_state.vibe_summary = ""
                st.session_state.vibe_confirmed = False
                st.rerun()
        with col_b:
            if st.button("✅ Lock In My Vibe & Proceed →", use_container_width=True, type="primary"):
                st.session_state.vibe_confirmed = True
                st.session_state.step = max(st.session_state.step, 2)
                set_nav_page("2. Budget Engine & Pie Chart")

    if st.session_state.vibe_confirmed:
        st.success("✅ Vibe locked! You can proceed to the Budget Engine.")
        if st.button("Go to Step 2: Budget Engine & Pie Chart →", type="secondary"):
            set_nav_page("2. Budget Engine & Pie Chart")


# =============================================================================
# STEP 2 — 100-POINT PRIORITY BUDGET ENGINE
# =============================================================================
def render_step2() -> None:
    """Render Step 2: 100-Point Priority Budget Engine and allocation breakdown."""
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div class="step-banner" role="region" aria-label="Step 2: 100-Point Priority Budget Engine">
        <h2>💰 Step 2 — 100-Point Priority Budget Engine</h2>
        <p>Allocate exactly 100 points across your 4 core event categories.</p>
    </div>
    """, unsafe_allow_html=True)

    sym = currency_symbol()

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("#### 💵 Base Total Budget")
        budget = st.number_input(
            f"Total budget ({sym})",
            min_value=1000.0 if st.session_state.currency == "INR" else 10.0,
            max_value=100_000_000.0,
            value=float(st.session_state.total_budget),
            step=1000.0 if st.session_state.currency == "INR" else 10.0,
            format="%.0f",
            label_visibility="collapsed",
            disabled=st.session_state.budget_locked,
        )
        st.session_state.total_budget = budget
        st.markdown(f"<div class='info-box'>Total budget: <b>{fmt_amount(budget)}</b></div>",
                    unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🎯 Allocate Your 100 Points")
        st.caption("Higher points = higher budget priority = more protection during a crunch")

        # Sliders for 4 core categories
        for cat_key, cat_info in CATEGORIES.items():
            pts_key = f"points_{cat_key}"
            val = st.slider(
                cat_info["label"],
                min_value=0, max_value=100, step=5,
                value=int(st.session_state.get(pts_key, 0)),
                disabled=st.session_state.budget_locked,
                key=f"slider_{cat_key}",
            )
            st.session_state[pts_key] = val

        # Live total & validation
        current_total = total_points()
        st.markdown("---")
        if current_total == 100:
            st.success(f"✅ Perfect! All **100 points** allocated.")
        elif current_total < 100:
            remaining = 100 - current_total
            st.error(f"🔴 Total: **{current_total}/100** — assign **{remaining}** more points.")
        else:
            over = current_total - 100
            st.error(f"🔴 Total: **{current_total}/100** — reduce by **{over}** points.")

    with col_right:
        st.markdown("#### 📊 Budget Breakdown")
        pts = get_points_dict()
        fig = make_donut_chart(pts, budget, currency=st.session_state.currency)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Per-category breakdown table
        st.markdown("#### 📋 Category Allocations")
        for cat_key, cat_info in CATEGORIES.items():
            pts_val = int(st.session_state.get(f"points_{cat_key}", 0))
            amount  = points_to_amount(pts_val, budget)
            col_a, col_b, col_c = st.columns([2.5, 1, 1.5])
            col_a.markdown(cat_info["label"])
            col_b.markdown(f"**{pts_val}** pts")
            col_c.markdown(f"**{fmt_amount(amount)}**")

    st.markdown("")
    lock_disabled = (current_total != 100) or st.session_state.budget_locked
    if st.session_state.budget_locked:
        st.info("🔒 Budget is locked.")
        col_unlock, col_next = st.columns([1, 2])
        with col_unlock:
            if st.button("🔓 Unlock & Edit Budget"):
                st.session_state.budget_locked = False
                st.session_state.shield_result = None
                st.session_state.diy_cards = {}
                st.rerun()
        with col_next:
            if st.button("Go to Step 3: Priority Shield Simulator →", type="primary"):
                set_nav_page("3. Priority Shield Simulator")
    else:
        if st.button(
            "🔒 Lock Budget & Continue →",
            disabled=lock_disabled,
            type="primary",
            use_container_width=False,
        ):
            st.session_state.budget_locked = True
            st.session_state.step = max(st.session_state.step, 3)
            set_nav_page("3. Priority Shield Simulator")


def _render_diy_cards() -> None:
    """Render AI-powered DIY recommendation cards for compressed categories."""
    if not st.session_state.diy_cards:
        return
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("#### 💡 AI-Powered DIY Recommendation Cards")
    st.caption("Smart alternatives for your compressed categories — tailored to your vibe & Hard Nos")
    cols = st.columns(len(st.session_state.diy_cards))
    for i, (cat_key, card_data) in enumerate(st.session_state.diy_cards.items()):
        with cols[i]:
            saving = card_data["original"] - card_data["new"]
            st.markdown(f"""
            <div class="diy-card">
                <h5>💡 {card_data["label"]}</h5>
                <p style="font-size:0.83rem;color:#4b5563;margin-bottom:0.5rem;">
                    Saving ~{fmt_amount(saving)} | Budget: {fmt_amount(card_data["new"])}
                </p>
            </div>
            """, unsafe_allow_html=True)
            tips_text = card_data["tips"]
            for line in tips_text.split("\n"):
                clean_line = line.strip().lstrip("•-*").strip()
                if clean_line:
                    st.markdown(f"• {clean_line}")


# =============================================================================
# STEP 3 — WHAT-IF SIMULATOR & PRIORITY SHIELD
# =============================================================================
def render_step3() -> None:
    """Render Step 3: What-If Budget Drop Simulator and Priority Shield protection."""
    st.markdown("""
    <div class="step-banner" role="region" aria-label="Step 3: What-If Budget Drop Simulator">
        <h2>⚡ Step 3 — What-If Budget Drop Simulator</h2>
        <p>Simulate an unexpected budget cut. The Priority Shield protects your top priorities automatically.</p>
    </div>
    """, unsafe_allow_html=True)

    # Optional Budget Drop Toggle
    has_budget_drop = st.checkbox(
        "Did your budget experience an unexpected drop / cut?",
        value=st.session_state.get("has_budget_drop", False),
        key="has_budget_drop",
    )

    if not has_budget_drop:
        st.markdown("""
        <div style="background:#ecfdf5; border-left: 5px solid #10b981; border-radius: 10px; padding: 1.2rem 1.4rem; margin: 1.2rem 0; color: #065f46;">
            <h4 style="margin:0 0 0.4rem 0; color:#047857; font-size:1.05rem;">✅ Budget is stable!</h4>
            <p style="margin:0; font-size:0.95rem; line-height:1.5;">Budget is stable! No cuts simulated — your original allocations remain fully protected.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📋 Current Stable Allocations")
        pts = get_points_dict()
        allocs = {k: points_to_amount(v, st.session_state.total_budget) for k, v in pts.items()}
        cols = st.columns(4)
        for i, (k, info) in enumerate(CATEGORIES.items()):
            with cols[i]:
                st.metric(info["label"], fmt_amount(allocs[k]), f"{pts.get(k, 0)} pts")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Proceed to Step 4: Timeline & Quote Parser →", type="primary"):
            set_nav_page("4. Timeline & Quote Parser")
        return

    col_ctrl, col_info = st.columns([1, 1], gap="large")

    with col_ctrl:
        st.markdown("#### 📉 Simulate a Budget Drop")
        drop_pct = st.select_slider(
            "How much does your budget drop?",
            options=[10, 15, 20, 25, 30],
            value=st.session_state.drop_pct,
            format_func=lambda x: f"-{x}%",
        )
        st.session_state.drop_pct = drop_pct

        new_budget = st.session_state.total_budget * (1 - drop_pct / 100)
        deficit    = st.session_state.total_budget - new_budget

        col_a, col_b = st.columns(2)
        col_a.metric("Original Budget", fmt_amount(st.session_state.total_budget))
        col_b.metric(
            "After Drop",
            fmt_amount(new_budget),
            delta=f"-{fmt_amount(deficit)}",
            delta_color="inverse",
        )

        st.markdown("")
        st.markdown("""
        <div class="info-box">
        🛡️ <b>How the Priority Shield works:</b><br>
        Your <b>top 2 highest-priority categories</b> are fully protected.<br>
        The deficit is <b>proportionally distributed</b> across all compressible categories.<br>
        A <b>30% safety floor</b> prevents any category from dropping to zero.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("⚡ Run Priority Shield Simulation", type="primary", use_container_width=True):
            pts = get_points_dict()
            result = apply_priority_shield(pts, drop_pct, st.session_state.total_budget)
            st.session_state.shield_result = result
            st.session_state.step = max(st.session_state.step, 4)
            # Generate DIY cards for vulnerable categories that were actually funded
            diy_cards = {}
            for cat in result["vulnerable_cats"]:
                orig = result["original_allocs"].get(cat, 0.0)
                new  = result["new_allocs"].get(cat, 0.0)
                if orig > 0 and new < orig:
                    cat_label = CATEGORIES[cat]["label"]
                    prompt = f"""The user's {cat_label} budget was cut from {fmt_amount(orig)} to {fmt_amount(new)} due to an unexpected budget drop ({drop_pct}% overall).
Event type: {st.session_state.event_type}
Style preferences: {", ".join(st.session_state.style_tags) if st.session_state.style_tags else "not specified"}
Hard Nos: {st.session_state.hard_nos if st.session_state.hard_nos else "none"}

Suggest exactly 3 clever, creative, and practical DIY or local-vendor alternatives for {cat_label.split()[-1]} that:
- Save significant money without violating the Hard Nos
- Match the stated style preferences
- Are realistic for an Indian event (or general if not specified)
Format ONLY as 3 bullet points (•), each under 25 words. No headers."""
                    fallback_bullets = "\n".join(f"• {tip}" for tip in DIY_TEMPLATES.get(cat, [
                        "Explore local artisans for unique, cost-effective options.",
                        "DIY touches with good materials often outshine vendor quotes.",
                        "Community sharing / rentals can slash costs significantly.",
                    ]))
                    diy_cards[cat] = {
                        "label": cat_label,
                        "original": orig,
                        "new": new,
                        "tips": gemini_generate(prompt, fallback_bullets),
                    }
            st.session_state.diy_cards = diy_cards
            st.rerun()

    with col_info:
        if st.session_state.shield_result:
            result = st.session_state.shield_result
            st.markdown("#### 🛡️ Shield Status")
            for cat_key in CATEGORIES:
                label = CATEGORIES[cat_key]["label"]
                orig = result["original_allocs"].get(cat_key, 0.0)
                new  = result["new_allocs"].get(cat_key, 0.0)
                diff = new - orig
                diff_str = f" ({fmt_amount(diff)})" if diff < 0 else ""

                if orig == 0:
                    badge = '<span style="background:#4b5563;color:white;border-radius:6px;padding:2px 8px;font-size:0.75rem;font-weight:600;margin-left:6px;">⚪ EXCLUDED (0 PTS)</span>'
                elif cat_key in result["protected_cats"] and diff == 0:
                    badge = '<span class="badge-shield">🛡️ PROTECTED</span>'
                else:
                    badge = '<span class="badge-compressed">⚡ COMPRESSED</span>'

                st.markdown(
                    f"**{label}** {badge}<br>"
                    f"<small>{fmt_amount(orig)} → **{fmt_amount(new)}**{diff_str}</small>",
                    unsafe_allow_html=True,
                )
                st.markdown("")

            if result["remaining_deficit"] > 0:
                st.warning(
                    "⚠️ Maximum safe compression reached. Consider reducing top priorities slightly or lowering event scale."
                )
                st.caption(
                    f"💡 Unabsorbed deficit: {fmt_amount(result['remaining_deficit'])} (compressible categories are preserved at their 30% safety floor)."
                )
        else:
            st.markdown("""
            <div style="padding:2rem;text-align:center;color:#4b5563;">
                <div style="font-size:3rem;">⚡</div>
                <p>Run the simulation to see the Priority Shield in action.</p>
            </div>
            """, unsafe_allow_html=True)

    # Comparison chart + DIY cards
    if st.session_state.shield_result:
        result = st.session_state.shield_result
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Before vs After — Budget Comparison")
        fig = make_comparison_bar(
            result["original_allocs"],
            result["new_allocs"],
            result["protected_cats"],
            currency=st.session_state.currency,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        _render_diy_cards()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Proceed to Step 4: Timeline & Quote Parser →", type="primary"):
            set_nav_page("4. Timeline & Quote Parser")


# =============================================================================
# STEP 4A — SMART TIMELINE
# =============================================================================
def _render_task_row(idx: int, task_info: Dict[str, Any], event_date: date) -> None:
    """Render a single event task row with status, due date, and dependency indicator."""
    days_before = task_info["days_before"]
    task_name   = task_info["task"]
    category    = task_info["category"]
    depends_on  = task_info["depends_on"]
    task_date   = event_date - timedelta(days=days_before)
    days_until  = (task_date - date.today()).days

    # Check widget state directly for instantaneous reactivity
    is_done = bool(st.session_state.get(f"task_{idx}", False))

    # Urgency classification
    if is_done:
        urgency_label = "✅"
        urgency_class = "task-done"
    elif days_until < 0:
        urgency_label = "🔴 OVERDUE"
        urgency_class = "task-overdue"
    elif days_until <= 14:
        urgency_label = "🟠 DUE SOON"
        urgency_class = "task-urgent"
    else:
        urgency_label = "🟢 On Track"
        urgency_class = "task-ontrack"

    col_check, col_detail, col_date_col, col_status = st.columns([0.4, 3, 1.5, 1.5])

    with col_check:
        checked = st.checkbox(
            f"Mark {task_name} completed",
            key=f"task_{idx}",
            label_visibility="collapsed",
        )
        st.session_state.task_done[idx] = checked

    with col_detail:
        dep_str = ""
        if depends_on:
            escaped_dep = html.escape(str(", ".join(depends_on[:1])))
            dep_str = f" <span style='color:#4b5563;font-size:0.8rem;'>→ after: {escaped_dep}</span>"
        escaped_task = html.escape(str(task_name))
        escaped_cat = html.escape(str(category))
        st.markdown(
            f"<span class='{urgency_class}'>{escaped_task}</span>"
            f" <span style='background:#f3f4f6;border-radius:4px;padding:1px 6px;"
            f"font-size:0.78rem;color:#4b5563;'>{escaped_cat}</span>"
            f"{dep_str}",
            unsafe_allow_html=True,
        )

    with col_date_col:
        if days_before == 0:
            st.markdown("**📌 Event Day**")
        else:
            st.markdown(
                f"<span style='font-size:0.87rem;color:#4b5563;'>"
                f"{task_date.strftime('%d %b %Y')}</span>",
                unsafe_allow_html=True,
            )

    with col_status:
        st.markdown(
            f"<span style='font-size:0.83rem;'>{urgency_label}</span>",
            unsafe_allow_html=True,
        )


def render_step4_timeline() -> None:
    """Render Step 4A: Smart Event Timeline with dependency awareness."""
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div class="step-banner" role="region" aria-label="Step 4A: Smart Event Timeline">
        <h2>📅 Step 4A — Smart Event Timeline</h2>
        <p>Track every task with dependency awareness and urgency-coloured status.</p>
    </div>
    """, unsafe_allow_html=True)

    col_date, col_prog = st.columns([1, 1], gap="large")

    with col_date:
        st.markdown("#### 🗓️ When is your event?")
        event_date = st.date_input(
            "Event Date",
            value=st.session_state.event_date,
            min_value=date.today(),
            label_visibility="collapsed",
        )
        st.session_state.event_date = event_date
        days_to_go = (event_date - date.today()).days
        if days_to_go > 0:
            st.metric("Days to Go", f"{days_to_go} days")
        else:
            st.success("🎉 Event day is today or has passed!")

    tasks = TASK_TEMPLATES.get(
        st.session_state.event_type,
        TASK_TEMPLATES.get("Wedding"),
    )

    # Detect event type change to avoid stale checklist states
    if st.session_state.get("last_timeline_event_type") != st.session_state.event_type:
        for k in list(st.session_state.keys()):
            if k.startswith("task_"):
                del st.session_state[k]
        st.session_state.task_done = {}
        st.session_state.last_timeline_event_type = st.session_state.event_type

    # Completion stats: evaluate directly from widget state keys
    done_count = sum(
        1 for idx in range(len(tasks))
        if st.session_state.get(f"task_{idx}", False)
    )
    completion_pct = int((done_count / len(tasks)) * 100) if tasks else 0

    with col_prog:
        st.markdown("#### 📈 Overall Progress")
        st.progress(completion_pct / 100)
        st.metric("Tasks Completed", f"{done_count} / {len(tasks)}", f"{completion_pct}%")

    st.markdown("---")
    st.markdown("#### ✅ Task Checklist")
    st.caption("Tasks are sorted chronologically. Dependencies are shown with → arrows.")

    # Render individual task rows
    for idx, task_info in enumerate(tasks):
        _render_task_row(idx, task_info, event_date)


# =============================================================================
# STEP 4B — VENDOR QUOTE PARSER
# =============================================================================
def _render_quote_results(result: Dict[str, Any]) -> None:
    """Render structured vendor quote analysis results, line items table, and warnings."""
    st.markdown("#### 📊 Parsed Breakdown")
    items = result["items"]
    if items:
        # Build HTML table with accessibility attributes
        rows_html = ""
        for item in items:
            row_class = "tax-row" if item["is_tax"] else ("warn-row" if item["is_total"] else "")
            tag = ""
            if item["is_tax"]:
                tag = "🧾 Tax"
            elif item["is_total"]:
                tag = "📌 Total"
            rows_html += f"""
            <tr class="{row_class}">
                <td>{html.escape(str(item['name']))}</td>
                <td style="text-align:right;">{fmt_amount(item['amount'])}</td>
                <td style="font-size:0.82rem;color:#4b5563;">{tag}</td>
            </tr>"""

        st.markdown(f"""
        <table class="vendor-table" role="table" aria-label="Vendor Quote Breakdown">
            <thead>
                <tr>
                    <th scope="col">Item</th>
                    <th scope="col" style="text-align:right;">Amount</th>
                    <th scope="col">Type</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)
        st.markdown("")
        st.metric("Estimated Subtotal (excl. taxes)", fmt_amount(result["subtotal"]))
    else:
        st.info("No structured line items detected. Try a cleaner format (e.g., `Item Name: ₹12,000`).")

    # Missing items
    if result["missing_items"]:
        st.markdown("---")
        st.markdown("#### ⚠️ Possibly Missing Items")
        st.caption(f"Expected for a {html.escape(str(st.session_state.event_type))} but not found in this quote:")
        for m in result["missing_items"]:
            st.markdown(f"• **{m}** — not mentioned in the quote")

    # Hidden charge flags
    if result["hidden_flags"]:
        st.markdown("---")
        st.markdown("#### 🔍 Hidden Cost Watchlist")
        for flag in result["hidden_flags"]:
            st.markdown(flag)

    # AI commentary
    if result.get("ai_commentary"):
        st.markdown("---")
        st.markdown("#### 🤖 AI Advisor Notes")
        for line in result["ai_commentary"].split("\n"):
            clean_line = line.strip().lstrip("•-*").strip()
            if clean_line:
                st.markdown(f"• {clean_line}")


def render_step4_vendor() -> None:
    """Render Step 4B: Vendor Quote Analyzer and line-item auditor."""
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div class="step-banner" role="region" aria-label="Step 4B: Vendor Quote Analyzer">
        <h2>🔍 Step 4B — Vendor Quote Analyzer</h2>
        <p>Paste a messy vendor quote and we'll extract line items, taxes, and hidden cost warnings.</p>
    </div>
    """, unsafe_allow_html=True)

    col_input, col_output = st.columns([1, 1.2], gap="large")

    with col_input:
        st.markdown("#### 📄 Paste Your Vendor Quote")
        if st.button("📋 Load Sample Quote", help="Loads a demo quote so you can try the analyzer"):
            st.session_state.vendor_quote_text = SAMPLE_VENDOR_QUOTE
            st.session_state.vendor_parse_result = None
            st.rerun()

        quote_text = st.text_area(
            "Vendor Quote",
            value=st.session_state.vendor_quote_text,
            height=280,
            placeholder="Paste any vendor quote text here — messy formats are fine…",
            label_visibility="collapsed",
        )
        st.session_state.vendor_quote_text = quote_text

        analyze_disabled = not quote_text.strip()
        if st.button("🔍 Analyze Quote", type="primary", disabled=analyze_disabled,
                     use_container_width=True):
            with st.spinner("Parsing your quote…"):
                parse_result = parse_vendor_quote(quote_text, st.session_state.event_type)

                # If Gemini available, enhance with AI commentary
                if st.session_state.gemini_key and _GENAI_AVAILABLE:
                    ai_prompt = f"""You are an expert event budget advisor.
A vendor sent this quote for a {st.session_state.event_type}:

{quote_text[:1500]}

In 3-4 bullet points (•), identify:
1. Any potentially hidden or missing charges
2. Items that seem overpriced for an Indian market
3. What should be clarified or negotiated
Be concise (each bullet under 25 words). Start each bullet with •."""
                    ai_commentary = gemini_generate(ai_prompt, "")
                    parse_result["ai_commentary"] = ai_commentary
                else:
                    parse_result["ai_commentary"] = ""

                st.session_state.vendor_parse_result = parse_result
                st.rerun()

    with col_output:
        result = st.session_state.vendor_parse_result
        if result is None:
            st.markdown("""
            <div style="padding:3rem;text-align:center;color:#4b5563;">
                <div style="font-size:3rem;">📋</div>
                <p>Paste a quote on the left and click Analyze.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            _render_quote_results(result)


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================
def main() -> None:
    """Main entry point orchestrating session state, sidebar navigation, and step routing."""
    init_session_state()
    render_sidebar()

    # App header
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0 1.5rem;">
        <h1 style="font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,#667eea,#764ba2);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;">
            🎉 AI Event Planner
        </h1>
        <p style="color:#6b7280;margin:0.3rem 0 0;font-size:1rem;">
            Your AI-powered event planning assistant
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Route according to Sidebar Navigation Radio Menu
    current_page = st.session_state.get("nav_page", "1. Vibe Calibration")

    if current_page == "1. Vibe Calibration":
        render_step1()
    elif current_page == "2. Budget Engine & Pie Chart":
        render_step2()
    elif current_page == "3. Priority Shield Simulator":
        render_step3()
    elif current_page == "4. Timeline & Quote Parser":
        render_step4_timeline()
        render_step4_vendor()
    else:
        render_step1()

    # Footer
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;color:#4b5563;font-size:0.82rem;padding:0.5rem;'>"
        "🎉 AI Event Planner · Built for <b>Google for Developers Build with AI Challenge 5</b> · "
        "Powered by <b>Streamlit</b> + <b>Google Gemini</b>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
