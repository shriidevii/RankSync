#!/usr/bin/env python3
"""
RankSync — Redrob Hackathon Ranker
=====================================
Track: Intelligent Candidate Discovery & Ranking

Architecture:
  Stage 1 — Honeypot detection  (impossible profiles → excluded)
  Stage 2 — Career flags         (JD-explicit disqualifiers → penalty multipliers)
  Stage 3 — Six component scores (all 0-1, RAW, honest)
  Stage 4 — Weighted sum + penalty multipliers
  Stage 5 — Sort → top 100 → enforce monotonicity → reasoning → CSV

Key design principle:
  Company prestige ONLY helps when paired with an AI/ML title.
  A Java Developer at Swiggy is NOT a better fit than a Data Scientist at an
  unknown startup — the JD scores the role, not the brand.

Weights: career 32% | skill 28% | behavioral 22% | experience 8% | education 5% | location 5%

Runtime on 100k candidates: ~60-90s (CPU only, zero dependencies beyond stdlib)
"""

import gzip, json, csv, math, datetime, argparse, sys, os

TODAY = datetime.date(2026, 6, 20)

WEIGHTS = {
    "career":      0.32,
    "skill":       0.28,
    "behavioral":  0.22,
    "experience":  0.08,
    "education":   0.05,
    "location":    0.05,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

# ── JD SKILL TAXONOMY ─────────────────────────────────────────────────────────

TIER1_SKILLS = frozenset({
    "embeddings", "embedding", "semantic search", "dense retrieval",
    "vector search", "sentence-transformers", "sentence transformers", "bge", "e5",
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "faiss", "chromadb", "pgvector",
    "learning to rank", "bm25", "hybrid search", "information retrieval",
    "ranking", "reranking", "re-ranking", "ndcg", "mrr",
    "python", "recommendation systems", "mlops",
    "a/b testing", "evaluation frameworks", "offline evaluation",
})

TIER2_SKILLS = frozenset({
    "lora", "qlora", "peft", "fine-tuning", "fine-tune",
    "pytorch", "tensorflow", "scikit-learn", "xgboost",
    "rag", "llm", "llms", "langchain", "deep learning", "transformers", "nlp",
    "machine learning",
    "kafka", "airflow", "spark", "kubernetes", "docker",
})

# Skills that dominate → penalize (JD: not a CV/speech role)
CV_SPEECH_SKILLS = frozenset({
    "computer vision", "image classification", "object detection",
    "speech recognition", "tts", "asr", "robotics", "image segmentation",
    "ocr", "pose estimation", "gans", "image generation",
})

# ── TITLES ─────────────────────────────────────────────────────────────────────

AI_ML_TITLES = frozenset({
    "ml engineer", "machine learning engineer", "ai engineer", "data scientist",
    "nlp engineer", "search engineer", "applied ml engineer", "applied scientist",
    "research engineer", "recommendation systems engineer", "applied research engineer",
    "senior data scientist", "lead ml", "principal ml", "staff ml",
    "senior ml", "senior ai", "lead ai", "deep learning engineer",
    "ml scientist", "ai scientist", "ai research engineer", "junior ml engineer",
    "computer vision engineer",
})

RESEARCH_TITLES = frozenset({
    "research scientist", "postdoctoral", "postdoc",
    "academic researcher", "research associate", "phd researcher",
})

# Titles that are clearly non-AI (the main trap in 100k dataset)
NON_AI_TITLES = frozenset({
    "marketing manager", "sales executive", "hr manager", "accountant",
    "mechanical engineer", "civil engineer", "graphic designer", "ux designer",
    "customer support", "customer success", "project manager", "operations manager",
    "content writer", "content manager", "frontend engineer", "backend engineer",
    "java developer", ".net developer", "full stack developer", "devops engineer",
    "qa engineer", "mobile developer", "android developer", "ios developer",
    "web developer", "cloud engineer", "data analyst", "business analyst",
    "finance manager", "supply chain", "product manager",
})

# ── COMPANIES ──────────────────────────────────────────────────────────────────

PRODUCT_AI_COMPANIES = frozenset({
    "google", "microsoft", "amazon", "meta", "apple", "netflix",
    "flipkart", "swiggy", "zomato", "meesho", "ola", "uber",
    "razorpay", "cred", "phonepe", "paytm", "nykaa", "myntra",
    "freshworks", "zoho", "sarvam", "krutrim", "unacademy", "upgrad",
    "byju", "byjus", "haptik", "rephrase", "mad street den", "aganitha",
    "locobuzz", "inmobi", "wysa", "glance", "slice", "groww", "zepto",
    "dream11", "sharechat", "dailyhunt", "verloop", "saarthi", "niramai",
    "vedantu", "linkedin", "salesforce", "genpact ai", "policybazaar",
    "pharmeasy", "lenskart", "mfine", "khatabook", "udaan", "delhivery",
    "porter", "dunzo", "ixigo", "cleartrip", "healthkart", "practo",
})

CONSULTING_COMPANIES = frozenset({
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "tech mahindra", "mphasis",
    "hexaware", "l&t infotech", "ltimindtree", "coforge", "mindtree",
    "niit", "birlasoft", "mastech", "kpit",
})

# ── CAREER DESCRIPTION EVIDENCE ───────────────────────────────────────────────

CAREER_KW_HIGH = frozenset({
    # Retrieval/search (core JD requirement)
    "recommendation system", "retrieval system", "search ranking",
    "candidate retrieval", "vector search", "ann search",
    "approximate nearest neighbour", "approximate nearest neighbor",
    "information retrieval", "semantic search", "hybrid search",
    "learning to rank", "re-ranking", "reranking",
    # Specific tech deployed in production (not just "I know Kafka")
    "elasticsearch index", "opensearch index", "faiss index",
    "milvus collection", "qdrant collection", "weaviate schema",
    "embedding pipeline", "embedding model", "embedding space",
    "bm25", "ndcg", "mrr@", "recall@", "precision@",
    # Production signals
    "deployed to production", "shipped to production", "served in production",
    "real-time inference", "low latency serving", "model serving",
    "a/b test", "online experiment", "offline evaluation",
    "fine-tun", "lora", "qlora",
})

CAREER_KW_MED = frozenset({
    "pytorch", "tensorflow", "transformers", "machine learning model",
    "deep learning", "model training", "experiment tracking", "mlflow",
    "feature engineering", "bert", "gpt", "llm", "rag pipeline",
    "vector database", "sentence-transformer", "mlops pipeline",
})

# ── LOCATION ──────────────────────────────────────────────────────────────────

PREFERRED_CITIES = frozenset({"pune", "noida", "delhi", "gurgaon", "gurugram", "new delhi"})
GOOD_INDIA_CITIES = frozenset({
    "hyderabad", "bangalore", "bengaluru", "mumbai", "chennai",
    "ahmedabad", "kolkata", "indore", "chandigarh", "bhubaneswar",
    "vizag", "coimbatore", "trivandrum", "jaipur", "kochi",
})



def title_is_ai(title: str) -> bool:
    tl = title.lower()
    return any(kw in tl for kw in AI_ML_TITLES)

def title_is_non_ai(title: str) -> bool:
    tl = title.lower()
    return any(kw in tl for kw in NON_AI_TITLES)

def title_is_research_only(title: str) -> bool:
    tl = title.lower()
    return any(kw in tl for kw in RESEARCH_TITLES)

def company_is_product_ai(company: str) -> bool:
    cl = company.lower()
    return any(pc in cl for pc in PRODUCT_AI_COMPANIES)

def company_is_consulting(company: str) -> bool:
    cl = company.lower()
    return any(c in cl for c in CONSULTING_COMPANIES)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1: HONEYPOT DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_honeypot(candidate: dict) -> tuple[bool, str]:
    """
    Four independent checks for the ~80 honeypots in the 100k dataset.
    We err conservative (false negatives allowed) to avoid disqualifying
    legitimate candidates.
    """
    profile  = candidate.get("profile", {})
    skills   = candidate.get("skills", [])
    career   = candidate.get("career_history", [])
    signals  = candidate.get("redrob_signals", {})

    # Check A: Many expert skills with BOTH zero duration AND zero endorsements
    expert_ghost = sum(
        1 for s in skills
        if s.get("proficiency") in ("advanced", "expert")
        and s.get("duration_months", 1) == 0
        and s.get("endorsements", 0) == 0
    )
    if expert_ghost >= 5:
        return True, f"A: {expert_ghost} expert skills with 0 duration & 0 endorsements"

    # Check B: Total career months impossible given stated YoE
    total_months = sum(max(0, j.get("duration_months", 0)) for j in career)
    yoe = float(profile.get("years_of_experience", 0))
    if yoe > 0 and total_months > 0:
        if (total_months / 12) > (yoe * 1.5 + 2) and (total_months / 12) > 15:
            return True, f"B: {total_months}mo career impossible for YoE={yoe}"

    # Check C: Assessment score contradicts expert proficiency
    skill_map = {s["name"].lower(): s for s in skills}
    for skill_name, score in signals.get("skill_assessment_scores", {}).items():
        s = skill_map.get(skill_name.lower(), {})
        if s.get("proficiency") == "expert" and score < 10:
            return True, f"C: expert '{skill_name}' but assessment={score:.0f}/100"

    # Check D: Impossible date ranges
    for job in career:
        try:
            start = datetime.date.fromisoformat(job.get("start_date", "1970-01-01"))
            end_raw = job.get("end_date")
            if end_raw:
                end = datetime.date.fromisoformat(end_raw)
                if end < start:
                    return True, f"D: end {end} < start {start}"
            if start > TODAY:
                return True, f"D: future start_date {start}"
        except (ValueError, TypeError):
            pass

    return False, ""


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2: CAREER FLAGS
# ══════════════════════════════════════════════════════════════════════════════

def compute_career_flags(profile: dict, career: list) -> dict:
    flags = {
        "consulting_only":        False,
        "pure_research_only":     False,
        "title_chaser":           False,
        "no_ai_career_evidence":  False,
    }
    if not career:
        flags["no_ai_career_evidence"] = True
        return flags

    # Consulting only
    non_consulting = [j for j in career if not company_is_consulting(j.get("company",""))]
    flags["consulting_only"] = (len(non_consulting) == 0)

    # Pure research only
    non_research = [j for j in career if not title_is_research_only(j.get("title",""))]
    flags["pure_research_only"] = (len(non_research) == 0)

    # Title chaser: avg tenure < 14mo across 3+ jobs
    if len(career) >= 3:
        durations = [j.get("duration_months", 0) for j in career]
        flags["title_chaser"] = (sum(durations) / len(durations)) < 14

    # No AI career evidence: no AI title AND no strong description evidence
    has_ai_title = any(title_is_ai(j.get("title","")) for j in career)
    has_desc_evidence = False
    for j in career:
        desc = j.get("description","").lower()
        if sum(1 for kw in CAREER_KW_HIGH if kw in desc) >= 2:
            has_desc_evidence = True
            break
    flags["no_ai_career_evidence"] = (not has_ai_title and not has_desc_evidence)

    return flags


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3: COMPONENT SCORES
# ══════════════════════════════════════════════════════════════════════════════

def score_career(career: list, flags: dict) -> float:
    """
    CRITICAL FIX: Company prestige only applies when title is AI-aligned.
    A Java Developer at Swiggy gets company_s = 0.50 (unknown/neutral),
    not 1.0 — the brand doesn't make the role relevant.
    """
    if not career:
        return 0.0

    total_score  = 0.0
    total_weight = 0.0

    for job in career:
        duration = max(job.get("duration_months", 1), 1)
        weight   = math.log1p(duration)

        title   = job.get("title", "")
        company = job.get("company", "")
        desc    = job.get("description", "").lower()

        # ── A. Title score (0-1) ──────────────────────────────────
        if title_is_ai(title):
            if title_is_research_only(title):
                title_s = 0.20   # research title penalty
            else:
                title_s = 1.00
        elif any(x in title.lower() for x in ["engineer", "scientist", "developer", "analyst"]):
            title_s = 0.15 
        else:
            title_s = 0.03  

        # ── B. Company score (0-1) — GATED BY TITLE RELEVANCE ────
 
        if company_is_consulting(company):
            company_s = 0.08
        elif company_is_product_ai(company):
            # Gate: full credit only for AI titles; generic tech title gets 0.55
            if title_is_ai(title):
                company_s = 1.00
            elif not title_is_non_ai(title):
                company_s = 0.55  
            else:
                company_s = 0.35   
        else:
            company_s = 0.45  

        # ── C. Description evidence (0-1) ─────────────────────────
   
        high_hits = sum(1 for kw in CAREER_KW_HIGH if kw in desc)
        med_hits  = sum(1 for kw in CAREER_KW_MED  if kw in desc)
        desc_s    = min(1.0, high_hits * 0.18 + med_hits * 0.05)

        # ── Combine: title 40% + company 28% + description 32% ───
        job_s = 0.40 * title_s + 0.28 * company_s + 0.32 * desc_s
        total_score  += job_s * weight
        total_weight += weight

    raw = total_score / total_weight if total_weight > 0 else 0.0

    # Penalties
    if flags["consulting_only"]:
        raw *= 0.35
    if flags["pure_research_only"]:
        raw *= 0.15
    if flags["title_chaser"]:
        raw = max(0.0, raw - 0.30)

    return max(0.0, min(1.0, raw))


def score_skills(skills: list, signals: dict) -> float:
    """
    Depth-weighted JD alignment.
    depth(skill) = proficiency × duration × endorsements × assessment
    NOT a keyword count — volume alone does not help.
    """
    if not skills:
        return 0.0

    assessments = {k.lower(): v for k, v in signals.get("skill_assessment_scores", {}).items()}

    def depth(s: dict) -> float:
        name    = s.get("name", "").lower()
        prof    = s.get("proficiency", "beginner")
        prof_v  = {"beginner":0.20, "intermediate":0.50, "advanced":0.80, "expert":1.00}.get(prof, 0.20)
        dur_v   = min(1.0, s.get("duration_months", 0) / 48)
        end_v   = min(1.0, math.log1p(s.get("endorsements", 0)) / math.log1p(100))
        aval    = assessments.get(name, -1)
        assess_v = (aval / 100) if aval >= 0 else prof_v
        return 0.35 * prof_v + 0.30 * dur_v + 0.20 * end_v + 0.15 * assess_v

    tier1_score = 0.0
    tier2_score = 0.0
    tier1_count = 0
    cv_adv      = 0

    for s in skills:
        name_lower = s.get("name","").lower()
        d = depth(s)
        in_t1 = (name_lower in TIER1_SKILLS or
                 any(t in name_lower for t in TIER1_SKILLS if len(t) > 5))
        in_t2 = (not in_t1 and (name_lower in TIER2_SKILLS or
                 any(t in name_lower for t in TIER2_SKILLS if len(t) > 5)))
        in_cv = (name_lower in CV_SPEECH_SKILLS or
                 any(cv in name_lower for cv in CV_SPEECH_SKILLS if len(cv) > 4))

        if in_t1:
            tier1_score += d
            tier1_count += 1
        elif in_t2:
            tier2_score += d
        if in_cv and s.get("proficiency") in ("advanced","expert") and s.get("duration_months",0) >= 24:
            cv_adv += 1

    # 7 strong tier-1 matches = perfect (JD lists ~18 tier-1 skills; expect 6-9 matches)
    t1_norm = min(1.0, tier1_score / 7.0)
    t2_norm = min(1.0, tier2_score / 5.0)
    raw = 0.72 * t1_norm + 0.28 * t2_norm

    # CV domination penalty
    if cv_adv >= 2 and cv_adv > max(1, tier1_count):
        raw *= 0.20

    return max(0.0, min(1.0, raw))


def score_behavioral(signals: dict) -> float:
    """
    The 'behavioral twin' trap killer (JD: inactive + low RR = not available).
    """
    # Recency
    try:
        last = datetime.date.fromisoformat(signals.get("last_active_date","2000-01-01"))
        days = max(0, (TODAY - last).days)
    except (ValueError, TypeError):
        days = 999

    if   days <=  7:  recency = 1.00
    elif days <= 14:  recency = 0.92
    elif days <= 30:  recency = 0.80
    elif days <= 60:  recency = 0.58
    elif days <= 90:  recency = 0.35
    elif days <= 180: recency = 0.12
    else:             recency = 0.02

    otw = 1.0 if signals.get("open_to_work_flag", False) else 0.40

    rr = float(signals.get("recruiter_response_rate", 0.0))
    if   rr >= 0.85: rr_s = 1.00
    elif rr >= 0.70: rr_s = 0.85
    elif rr >= 0.55: rr_s = 0.68
    elif rr >= 0.40: rr_s = 0.50
    elif rr >= 0.25: rr_s = 0.30
    elif rr >= 0.10: rr_s = 0.14
    else:            rr_s = 0.03

    notice = int(signals.get("notice_period_days", 60))
    if   notice ==  0: notice_s = 1.00
    elif notice <= 15: notice_s = 0.95
    elif notice <= 30: notice_s = 0.88
    elif notice <= 45: notice_s = 0.72
    elif notice <= 60: notice_s = 0.56
    elif notice <= 90: notice_s = 0.38
    elif notice <=120: notice_s = 0.22
    else:              notice_s = 0.08

    gh = float(signals.get("github_activity_score", -1))
    if   gh == -1:  gh_s = 0.22
    elif gh >= 80:  gh_s = 1.00
    elif gh >= 60:  gh_s = 0.82
    elif gh >= 40:  gh_s = 0.60
    elif gh >= 20:  gh_s = 0.40
    else:           gh_s = 0.20

    icr  = float(signals.get("interview_completion_rate", 0.5))
    resp = max(0.0, 1.0 - float(signals.get("avg_response_time_hours", 72)) / 168)
    saved = int(signals.get("saved_by_recruiters_30d", 0))
    views = int(signals.get("profile_views_received_30d", 0))
    eng_s = min(1.0, (math.log1p(saved)*0.6 + math.log1p(views)*0.4) / math.log1p(30))

    beh = (
        0.28 * recency  +
        0.20 * rr_s     +
        0.18 * otw      +
        0.16 * notice_s +
        0.09 * gh_s     +
        0.05 * icr      +
        0.02 * resp     +
        0.02 * eng_s
    )

    # Hard cap: not-open-to-work AND inactive 90+d = effectively unavailable
    if not signals.get("open_to_work_flag", False) and days > 90:
        beh = min(beh, 0.28)

    return max(0.0, min(1.0, beh))


def score_experience(profile: dict, flags: dict) -> float:
    yoe = float(profile.get("years_of_experience", 0))
    if   6.0 <= yoe <= 8.0:   base = 1.00
    elif 5.0 <= yoe <  6.0:   base = 0.88
    elif 8.0 <  yoe <= 9.5:   base = 0.85
    elif 4.0 <= yoe <  5.0:   base = 0.72
    elif 9.5 <  yoe <= 11.0:  base = 0.62
    elif 3.0 <= yoe <  4.0:   base = 0.50
    elif 11.0 < yoe <= 14.0:  base = 0.45
    elif 14.0 < yoe <= 18.0:  base = 0.30
    elif yoe > 18.0:           base = 0.18
    else:                      base = 0.15
    if flags["pure_research_only"]:
        base *= 0.20
    return min(1.0, base)


def score_education(education: list) -> float:
    if not education:
        return 0.35
    CS_FIELDS = frozenset({
        "computer science","information technology","electronics",
        "electrical engineering","computer engineering","software engineering",
        "mathematics","statistics","data science","machine learning",
        "artificial intelligence","computational mathematics",
    })
    best = 0.0
    for edu in education:
        tier_v = {"tier_1":1.00,"tier_2":0.75,"tier_3":0.50,
                  "tier_4":0.28,"unknown":0.38}.get(edu.get("tier","unknown"), 0.38)
        field  = edu.get("field_of_study","").lower()
        bonus  = 0.12 if any(f in field for f in CS_FIELDS) else 0.0
        best   = max(best, min(1.0, tier_v + bonus))
    return best


def score_location(profile: dict, signals: dict) -> float:
    location = profile.get("location","").lower()
    country  = profile.get("country","").lower()
    relocate = signals.get("willing_to_relocate", False)

    is_india = ("india" in country or country == "in")
    if not is_india:
        return 0.45 if relocate else 0.20

    if any(c in location for c in PREFERRED_CITIES):  return 1.00
    if any(c in location for c in GOOD_INDIA_CITIES): return 0.78 if not relocate else 0.86
    return 0.55 if relocate else 0.42


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4: FINAL SCORE
# ══════════════════════════════════════════════════════════════════════════════

def compute_final(scores: dict, flags: dict, profile: dict) -> float:
    raw = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)

    
    if flags["no_ai_career_evidence"]:
        current_title = profile.get("current_title","")
        if title_is_non_ai(current_title):
            raw *= 0.10   # Marketing Manager w/ AI skills → disqualified
        else:
            raw *= 0.45   # Title is neutral (unknown); give some benefit of doubt

    # Pure research (JD: "tried it twice, didn't work")
    if flags["pure_research_only"]:
        raw *= 0.15

    # Consulting-only cap
    if flags["consulting_only"]:
        raw = min(raw, 0.32)

    # Title-chaser: loyalty concern
    if flags["title_chaser"]:
        raw *= 0.75

    return max(0.0, min(1.0, raw))


# ══════════════════════════════════════════════════════════════════════════════
# SCORE ONE CANDIDATE
# ══════════════════════════════════════════════════════════════════════════════

def score_candidate(candidate: dict) -> dict:
    cid      = candidate.get("candidate_id","UNKNOWN")
    profile  = candidate.get("profile", {})
    career   = candidate.get("career_history", [])
    education= candidate.get("education", [])
    skills   = candidate.get("skills", [])
    signals  = candidate.get("redrob_signals", {})

    is_hp, hp_reason = detect_honeypot(candidate)
    if is_hp:
        return {"candidate_id": cid, "final_score": -1.0,
                "is_honeypot": True, "hp_reason": hp_reason, "_candidate": candidate}

    flags = compute_career_flags(profile, career)

    s = {
        "career":     score_career(career, flags),
        "skill":      score_skills(skills, signals),
        "behavioral": score_behavioral(signals),
        "experience": score_experience(profile, flags),
        "education":  score_education(education),
        "location":   score_location(profile, signals),
    }
    final = compute_final(s, flags, profile)

    return {"candidate_id": cid, "final_score": final, "is_honeypot": False,
            **s, "flags": flags, "_candidate": candidate}


# ══════════════════════════════════════════════════════════════════════════════
# REASONING GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_reasoning(candidate: dict, result: dict, rank: int) -> str:
    p      = candidate["profile"]
    sig    = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    flags  = result.get("flags", {})

    title   = p.get("current_title","")
    company = p.get("current_company","")
    yoe     = p.get("years_of_experience", 0)
    loc     = p.get("location","")
    rr      = float(sig.get("recruiter_response_rate", 0))
    notice  = int(sig.get("notice_period_days", 60))
    github  = float(sig.get("github_activity_score", -1))
    otw     = sig.get("open_to_work_flag", False)

    try:
        last  = datetime.date.fromisoformat(sig.get("last_active_date","2000-01-01"))
        days  = max(0, (TODAY - last).days)
    except Exception:
        days = 999

    # Top matching skills from Tier 1
    jd_skills = [
        s["name"] for s in skills
        if s.get("name","").lower() in TIER1_SKILLS
        or any(t in s.get("name","").lower() for t in TIER1_SKILLS if len(t) > 5)
    ][:4]

    # Best career entry (longest AI-titled role)
    best_job = None
    for j in career:
        if title_is_ai(j.get("title","")):
            if best_job is None or j.get("duration_months",0) > best_job.get("duration_months",0):
                best_job = j

    strengths, concerns = [], []

    if jd_skills:
        strengths.append(f"JD skills: {', '.join(jd_skills[:3])}")
    if best_job:
        strengths.append(f"production AI at {best_job['company']} ({best_job['duration_months']}mo)")
    if otw and days <= 30:
        strengths.append("actively available")
    elif otw:
        strengths.append("open to work")
    if rr >= 0.75:
        strengths.append(f"recruiter response rate {rr:.0%}")
    if notice <= 30:
        strengths.append(f"{notice}d notice")
    if github >= 60:
        strengths.append(f"GitHub {github:.0f}/100")

    if days > 60:
        concerns.append(f"inactive {days}d")
    if rr < 0.35:
        concerns.append(f"low RR ({rr:.0%})")
    if notice > 90:
        concerns.append(f"notice {notice}d")
    if not otw:
        concerns.append("not open to work")
    if flags.get("consulting_only"):
        concerns.append("consulting-only background")
    if flags.get("title_chaser"):
        concerns.append("avg tenure <14mo")
    if flags.get("no_ai_career_evidence"):
        concerns.append("no production AI/ML career evidence")
    if yoe > 13:
        concerns.append(f"overqualified ({yoe:.0f}yr)")
    if any(x in loc for x in ["Berlin","Toronto","Sydney","Austin","New York","Singapore"]):
        concerns.append("outside India")

    core = f"{yoe:.1f}yr {title} at {company}"

    if rank <= 10:
        s_str = "; ".join(strengths[:3]) or "strong overall fit"
        c_str = (f"; note: {concerns[0]}") if concerns else ""
        return f"{core}; {s_str}{c_str}."[:300]
    elif rank <= 30:
        s_str = "; ".join(strengths[:2]) or "moderate fit"
        c_str = (f"; {', '.join(concerns[:2])}") if concerns else ""
        return f"{core}; {s_str}{c_str}."[:300]
    elif rank <= 60:
        gap = (f"; gaps: {', '.join(concerns[:2])}") if concerns else "; partial JD fit"
        s_str = strengths[0] if strengths else "some relevant signals"
        return f"{core}; {s_str}{gap}."[:300]
    else:
        gap = "; ".join(concerns[:3]) or "below-average JD fit"
        return f"{core}; {gap}; marginal rank {rank} inclusion."[:300]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def load_candidates(path: str) -> list:
    opener = gzip.open if path.endswith(".gz") else open
    candidates = []
    try:
        with opener(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        candidates.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)
    return candidates


def rank_candidates(candidates_path: str, output_path: str):
    print(f"[1/4] Loading candidates: {candidates_path}")
    candidates = load_candidates(candidates_path)
    print(f"      Loaded {len(candidates):,}")

    print("[2/4] Scoring all candidates...")
    scored, honeypots = [], []
    for i, c in enumerate(candidates):
        r = score_candidate(c)
        (honeypots if r["is_honeypot"] else scored).append(r)
        if (i+1) % 20000 == 0:
            print(f"      {i+1:,}/{len(candidates):,}...")
    print(f"      Honeypots excluded : {len(honeypots)}")
    print(f"      Valid candidates   : {len(scored):,}")

    print("[3/4] Sorting, selecting top 100...")
    scored.sort(key=lambda x: (-x["final_score"], -x["career"], x["candidate_id"]))
    top100 = scored[:100]
    # Enforce strict non-increasing (spec requirement)
    for i in range(1, len(top100)):
        if top100[i]["final_score"] > top100[i-1]["final_score"]:
            top100[i]["final_score"] = top100[i-1]["final_score"]

    print(f"[4/4] Writing {output_path}...")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["candidate_id","rank","score","reasoning"])
        for rank, r in enumerate(top100, 1):
            c = r["_candidate"]
            writer.writerow([
                r["candidate_id"], rank,
                f"{r['final_score']:.4f}",
                generate_reasoning(c, r, rank),
            ])

    # ── Summary ───────────────────────────────────────────────────────────────
    is_mono = all(top100[i]["final_score"] >= top100[i+1]["final_score"] for i in range(len(top100)-1))
    print()
    print("=" * 70)
    print("  TALENTLENS — SUBMISSION SUMMARY")
    print("=" * 70)
    print(f"  Candidates processed  : {len(candidates):,}")
    print(f"  Honeypots excluded    : {len(honeypots)}")
    print(f"  Score range (top 100) : {top100[-1]['final_score']:.4f}  –  {top100[0]['final_score']:.4f}")
    print(f"  Monotonically non-↑   : {'✓ YES' if is_mono else '✗ FAIL'}")
    print(f"  Output                : {output_path}")
    print()
    print(f"  {'#':>3}  {'Candidate':<15}  {'Score':>6}  {'Career':>6}  "
          f"{'Skill':>6}  {'Beh':>6}  Title @ Company")
    print("  " + "─"*78)
    for i, r in enumerate(top100[:20], 1):
        p = r["_candidate"]["profile"]
        tc = f"{p['current_title']} @ {p['current_company']}"[:42]
        print(f"  {i:>3}  {r['candidate_id']:<15}  {r['final_score']:>6.4f}  "
              f"{r['career']:>6.3f}  {r['skill']:>6.3f}  {r['behavioral']:>6.3f}  {tc}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TalentLens — Redrob Hackathon Ranker")
    parser.add_argument("--candidates", required=True,
                        help="candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", default="submission.csv",
                        help="Output CSV (default: submission.csv)")
    args = parser.parse_args()

    if not os.path.exists(args.candidates):
        print(f"ERROR: not found: {args.candidates}", file=sys.stderr); sys.exit(1)

    rank_candidates(args.candidates, args.out)