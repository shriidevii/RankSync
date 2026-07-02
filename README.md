<div align="center">

# 🎯 RankSync — AI

### Intelligent Candidate Discovery & Ranking Engine

**Built for India.Runs 2026 · Redrob AI × Hack2Skill · Track 1: Data & AI Challenge**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Zero Dependencies](https://img.shields.io/badge/Core%20Engine-Zero%20Dependencies-10B981?style=flat-square)]()
[![Runtime](https://img.shields.io/badge/Runtime-58s%20on%20CPU-6366F1?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-gray?style=flat-square)]()

**Ranks 100,000 candidates in 58 seconds · Raw honest scores · Zero GPU · Zero pip installs**

</div>

---

## 📌 The Problem

A Series A startup, **Redrob AI**, needs to fill a Senior AI Engineer role from a pool of **100,000 candidates**. Keyword filters fail — a Java Developer with "AI" stuffed into their skills list scores the same as a real ML Engineer who shipped production recommendation systems. The system needs to go **beyond keyword matching** to understand career depth, behavioral availability, and genuine JD fit.

## ✅ Our Solution

**RankSync AI** — a 6-component weighted scoring engine that ranks all 100,000 candidates and produces an honest, defensible top-100 shortlist with unique per-candidate reasoning.

```
Career Evidence (32%)  +  Skill Depth (28%)  +  Behavioral Signals (22%)
+  Experience Fit (8%)  +  Education Tier (5%)  +  Location (5%)
= Final Score (raw, 0.0–1.0, no normalization)
```

| Metric | Value |
|---|---|
| Candidates scored | 100,000 |
| Runtime | **58 seconds** (CPU only, 5× under the 5-min limit) |
| Memory | < 2 GB |
| Dependencies (core engine) | **Zero** — Python stdlib only |
| Honeypots detected | ~90 |
| Top score | 0.9239 (Senior ML Engineer @ Zomato) |
| Rank 100 score | 0.7127 — top 0.1% of 100k, **not** a fake 0.01 |
| Score gaps | 39 unique values — proves real computation, not arithmetic |

---

## 🏗️ Architecture

```
candidates.jsonl (100k)
        │
        ▼
┌───────────────────────────┐
│  1. HONEYPOT DETECTOR     │   4 independent rules
│     ~90 profiles excluded │   (ghost expertise, impossible
└───────────┬───────────────┘   timeline, assessment fraud,
            │                   date anomalies)
            ▼
┌───────────────────────────┐
│  2. CAREER FLAG ENGINE    │   consulting-only · pure-research
│                           │   title-chaser · no-AI-evidence
└───────────┬───────────────┘
            ▼
┌───────────────────────────┐
│  3. SIX-COMPONENT SCORER  │   career · skill · behavioral
│     (all scores 0.0–1.0)  │   experience · education · location
└───────────┬───────────────┘
            ▼
┌───────────────────────────┐
│  4. PENALTY MULTIPLIERS   │   trap-detection penalties applied
└───────────┬───────────────┘   to the weighted sum
            ▼
┌───────────────────────────┐
│  5. SORT → TOP 100 →      │
│     REASONING → CSV       │
└───────────────────────────┘
```

### Key design decisions

- **No ML model training.** The JD provides explicit domain signals; a hand-crafted, explainable formula outperforms a black-box model with no ground-truth labels and produces deterministic, reproducible output.
- **Company prestige gated by job title.** `ML Engineer @ Swiggy` scores 1.0 on company quality; `Java Developer @ Swiggy` scores 0.35 — the brand alone doesn't inflate unrelated roles.
- **Depth-weighted skills, not keyword count.** `depth = proficiency × duration × endorsements × assessment`. An expert with 4 years beats a beginner with 1 month, even if both "have" the skill.
- **Raw scores, no cosmetic normalization.** Min-max forcing scores into 0.99→0.01 is misleading — it makes a top-0.1%-of-100k candidate look worthless. We report honest numbers instead.
- **Zero-hallucination reasoning.** Every claim in a candidate's reasoning string is pulled directly from their data fields — no generative AI, no inference, no invented facts.

---

## 📁 Repository Structure

```
RankSync/
├── backend/
│   ├── ranker/
│   │   └── rank.py              # Core scoring engine (single file, zero deps)
│   ├── dataset/
│   │   └── candidates.jsonl     # Input dataset (100k candidates)
│   └── output/
│       └── submission.csv       # Generated top-100 shortlist
├── frontend/
│   └── app.py                   # Streamlit dashboard (reads rank.py)
├── requirements.txt              # Dashboard-only deps (streamlit, pandas)
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/<your-username>/RankSync.git
cd RankSync
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run the ranker (core deliverable — zero extra dependencies)

```bash
python backend/ranker/rank.py \
  --candidates backend/dataset/candidates.jsonl \
  --out backend/output/submission.csv
```

Output: `submission.csv` with columns `candidate_id, rank, score, reasoning` — 100 rows, ranks 1–100, monotonically non-increasing scores, in **~58 seconds**.

### 3. Launch the dashboard

```bash
streamlit run frontend/app.py
```

Opens an interactive UI to explore the ranking: score breakdowns, career timelines, matched skills, behavioral signals, AI-generated reasoning, honeypot inspector, and one-click CSV export.

---

## 🧮 Scoring Methodology

| Component | Weight | What it measures |
|---|---|---|
| **Career Evidence** | 32% | Title quality × company quality (gated by title) × production-AI keywords in job descriptions, log-weighted by tenure |
| **Skill Match** | 28% | Depth-weighted tier-1/tier-2 JD skills: proficiency × duration × endorsements × assessment score |
| **Behavioral Signals** | 22% | 8 signals — recency, open-to-work flag, response rate, notice period, GitHub activity, interview completion, response speed, recruiter saves |
| **Experience Fit** | 8% | Bell curve peaking at 6–8yr (JD's stated ideal range) |
| **Education** | 5% | Institution tier (1–4) + CS/Engineering field bonus |
| **Location** | 5% | Pune/Noida = 1.0, major Indian cities = 0.78, outside India = 0.20–0.45 |

### Penalty multipliers

| Trigger | Penalty | JD Rationale |
|---|---|---|
| Non-AI title + no AI career evidence | × 0.10 | "A Marketing Manager with AI keywords is NOT a fit" |
| Pure research only | × 0.15 | "We tried it twice. Didn't work." |
| Consulting-only background | Capped at 0.35 | Need product-ownership mindset |
| Title-chaser (avg tenure < 14mo) | × 0.75 | Need 3+ year commitment |
| CV/Speech/Robotics skill dominance | × 0.20 on skill score | "This is NOT a computer vision role" |
| Inactive > 90 days, not open to work | Behavioral capped at 0.28 | "Inactive 6mo + 5% RR ≠ actually available" |

---

## 🍯 Honeypot Detection

Four independent checks catch the ~90 deliberately-impossible profiles seeded in the dataset:

| Rule | Trigger |
|---|---|
| **A — Ghost Expertise** | ≥5 skills marked "expert" with 0 duration AND 0 endorsements |
| **B — Impossible Timeline** | Total career months exceeds stated years of experience × 1.5 + 2 years |
| **C — Assessment Fraud** | "Expert" proficiency declared but platform assessment score < 10/100 |
| **D — Date Anomalies** | Job end date before start date, or a start date in the future |

---

## 📊 Sample Results — Top 3 Candidates

| Rank | Candidate | Score | Highlights |
|---|---|---|---|
| 1 | Senior ML Engineer @ Zomato | **0.9239** | 7.2yr · career 0.941, skill 0.958 · Weaviate, Recommendation Systems, Pinecone · open to work, 15d notice |
| 2 | Lead AI Engineer @ Razorpay | **0.8987** | 6.7yr · highest career score (0.961) · Information Retrieval, pgvector, Learning to Rank |
| 3 | Senior AI Engineer @ Apple | **0.8955** | 5.9yr · FAANG · FAISS, OpenSearch, Weaviate · actively available |

---

## ⚙️ Compute Constraints Compliance

| Constraint | Limit | Actual |
|---|---|---|
| Runtime | ≤ 5 min | **58 seconds** |
| Memory | ≤ 16 GB | **< 2 GB** |
| Compute | CPU only | ✅ Pure Python, no GPU ops |
| Network | Offline | ✅ Zero external calls |
| Reproducibility | Deterministic | ✅ Same input → same output, always |

---

## 🛠️ Tech Stack

**Core ranker:** Python 3.10+ standard library only — `json`, `csv`, `math`, `datetime`, `gzip`, `argparse`. No PyTorch, no scikit-learn, no API calls. Fully explainable and reproducible by design.

**Dashboard:** Streamlit + Pandas — zero build step, runs instantly with no Node.js or webpack required.

---

## 👥 Team RankSync

**Track:** Track 1 — Data & AI Challenge
**Hackathon:** India.Runs 2026 — Redrob AI × Hack2Skill

---

<div align="center">

*Built to tell the truth. Raw scores. Honest gaps. Real reasoning.*

</div>
