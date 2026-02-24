---
title: AI Hiring Agent
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---
# AI Hiring Intelligence Agent

An automated candidate ranking system that uses Google X-Ray Search for sourcing and LLM-based reasoning for candidate evaluation.

## 🚀 Setup

1.  **Install Python 3.10+**.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure API Keys**:
    - Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edit `.env` and add your keys:
    - Edit `.env` and add your keys:
        - `GROQ_API_KEY`: Required for intelligent scoring (Llama 3).
        - `SERPER_API_KEY`: Required for sourcing candidates from LinkedIn (via Serper.dev).

## 🏃 Usage

### 1. Source & Analyze (Full Flow)
To search for candidates on LinkedIn and immediately analyze them:
```bash
python -m src.main --role "Senior Python Engineer" --location "San Francisco" --limit 5
```

### 2. Analyze Existing Data (JSON Input)
If you already have a list of candidates (e.g., from a previous run or manual file):
```bash
python -m src.main --role "Product Manager" --input mock_candidates.json
```

## 📊 Output
The tool outputs a JSON array to stdout and saves it to `results.json`.

**Example Output:**
```json
{
  "candidate_id": "...",
  "overall_score": 85,
  "recommended_action": "Shortlist",
  "intent_analysis": { ... },
  "role_fit_analysis": { ... },
  "risk_flags": ["Job hopping"]
}
```

## ⚠️ Notes
- **Sourcing**: Uses Google Custom Search (X-Ray) to find public profiles. It is **100% safe** and does not log into LinkedIn.
- **Scoring**: Requires a **Groq API key**. Without it, the system runs in "Mock Mode" for testing.
