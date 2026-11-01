# 🎉 AI Event Planner
### Build with AI Challenge 5 — Google for Developers

A fully functional, polished **Streamlit** web application that acts as your AI-powered event planning assistant — backed by **Google Gemini**.

---

## ✨ Features

| Step | Feature |
|---|---|
| **Step 1** | Vibe Calibration — event type, custom event types, style tags, Hard Nos, AI Reality Preview |
| **Step 2** | 100-Point Budget Engine — interactive sliders across 4 core categories, live Plotly donut chart, validation |
| **Step 3** | What-If Budget Simulator — Priority Shield algorithm with 30% safety floor + DIY AI cards |
| **Step 4A** | Smart Timeline — date-aware task checklist with urgency tracking and reactive progress |
| **Step 4B** | Vendor Quote Analyzer — regex parser, tax breakdown table + Gemini AI commentary |

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+ (e.g., MSYS2 MinGW64: `C:\msys64\mingw64\bin\python3.exe`)

### 2. Set Up Virtual Environment
```powershell
# In the project directory:
C:\msys64\mingw64\bin\python3.exe -m venv .venv

# Install dependencies
.\.venv\bin\pip install -r requirements.txt
```

### 3. (Optional) Configure Gemini API Key
```powershell
# Copy the template
Copy-Item .env.example .env
# Edit .env and paste your key from https://aistudio.google.com/
```
> **Note:** The app also has a sidebar API key input — you don't need a `.env` file. All AI features fall back gracefully to smart templates if no key is provided.

### 4. Run the App
From PowerShell in the project directory (`ai-event-planner`):
```powershell
& ".\.venv\bin\python.exe" -m streamlit run app.py
```
Or:
```powershell
.\.venv\bin\streamlit.exe run app.py
```

The app opens automatically in your browser at **http://localhost:8501** 🎉

### 5. Run Unit Tests
```powershell
.\.venv\bin\python.exe -m pytest tests/test_app.py -v
```

---

## 📁 Project Structure

```
ai-event-planner/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── tests/
│   └── test_app.py     # Automated unit test suite
├── .env.example        # API key template
├── .gitignore
└── README.md
```

---

## 🛡️ Priority Shield Algorithm

When a budget drop is simulated:
1. The 4 core categories are **ranked by point allocation** (highest → lowest)
2. **Top 2 highest** = 🛡️ PROTECTED — budget untouched
3. **Bottom 2** = ⚡ COMPRESSED — absorb deficit proportionally down to a 30% safety floor
4. Categories with **0 points / ₹0 allocations** are **automatically excluded** from absorbing cuts
5. **AI Recommendation Cards** suggest DIY/local alternatives for compressed categories
6. Remaining deficit is flagged if lower-priority cuts reach the 30% safety floor

---

## 🔧 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Modern interactive web UI framework |
| `google-generativeai` | Gemini AI integration & LLM SDK |
| `requests` | Direct Gemini REST API fallback |
| `plotly` | Interactive donut and before/after comparison bar charts |
| `python-dotenv` | Local `.env` configuration support |
| `pytest` | Automated unit testing framework |

---

## 🤖 AI Features (powered by Gemini 1.5 Flash)

- **Reality Preview Summary** — personalized vibe description based on style tags & Hard Nos
- **DIY Recommendation Cards** — context-aware budget-saving alternatives
- **Vendor Quote AI Commentary** — flags hidden costs and negotiation opportunities

All AI features have **built-in template fallbacks** — the app is fully functional without a Gemini API key.

---

*Built with ❤️ using Streamlit + Google Gemini*
