from datetime import date, datetime
 
TODAY = date(2026, 6, 4)
 
TIER1_SKILLS = {
    "embeddings", "vector database", "information retrieval", "hybrid search",
    "bm25", "learning to rank", "ndcg", "mrr", "map", "pinecone", "weaviate",
    "qdrant", "milvus", "faiss", "elasticsearch", "opensearch", "rag",
    "fine-tuning llms", "lora", "qlora", "peft", "llm", "transformers",
    "pytorch", "tensorflow", "xgboost", "scikit-learn", "machine learning",
    "nlp", "deep learning", "python", "recommendation systems",
    "ranking systems", "a/b testing", "search", "retrieval", "ranking",
    "sentence-transformers",
}
 
CONSULTING_FIRMS = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mphasis", "hexaware",
}
 
DISQUALIFIER_SKILLS = {
    "computer vision", "speech recognition", "tts", "image classification",
    "object detection", "robotics", "solidworks", "creo", "ansys",
}
 
PRODUCT_INDUSTRIES = {
    "food delivery", "fintech", "software", "saas", "edtech", "e-commerce",
    "ai/ml", "gaming", "transportation", "conversational ai", "adtech",
}
 
AI_TITLES = {
    "ml engineer", "machine learning engineer", "ai engineer",
    "data scientist", "nlp engineer", "research engineer",
    "recommendation", "search engineer", "ranking engineer",
    "applied scientist", "applied ml",
}
 
JD_TERMS = [
    "retrieval", "ranking", "embedding", "vector", "search",
    "recommendation", "rag", "inference", "production", "deployed",
]
 
PROFICIENCY_WEIGHTS = {
    "expert": 1.0, "advanced": 0.8, "intermediate": 0.55, "beginner": 0.3,
}
 
TIER_SCORES = {
    "tier_1": 1.0, "tier_2": 0.7, "tier_3": 0.5, "tier_4": 0.3, "unknown": 0.4,
}
 
CS_FIELDS = {
    "computer science", "information technology", "electrical engineering",
    "electronics", "mathematics", "statistics", "data science",
    "artificial intelligence",
}
 
PREFERRED_CITIES = {
    "pune", "noida", "bangalore", "bengaluru", "hyderabad",
    "mumbai", "delhi", "gurugram", "gurgaon", "chennai",
}
 
 
def score_candidate(c: dict) -> dict:
    honey = _is_honeypot(c)
    consult = _is_consulting_only(c)
 
    skill_s = _skill_score(c)
    career_s = _career_score(c)
    beh_s = _behavioral_score(c)
    exp_s = _experience_score(c)
    edu_s = _education_score(c)
    loc_s = _location_score(c)
 
    raw = (
        0.35 * skill_s
        + 0.25 * career_s
        + 0.20 * beh_s
        + 0.12 * exp_s
        + 0.05 * edu_s
        + 0.03 * loc_s
    )
 
    consulting_pen = 0.5 if consult else 1.0
    honeypot_pen = 0.05 if honey else 1.0
    final = raw * consulting_pen * honeypot_pen
 
    return {
        "final_score": round(final, 6),
        "skill_score": round(skill_s, 4),
        "career_score": round(career_s, 4),
        "behavioral_score": round(beh_s, 4),
        "experience_score": round(exp_s, 4),
        "education_score": round(edu_s, 4),
        "location_score": round(loc_s, 4),
        "honeypot_flag": honey,
        "consulting_penalty": consulting_pen,
    }
 
 
def _skill_score(c: dict) -> float:
    skills = c.get("skills", [])
    sig = c.get("redrob_signals", {})
    assess = sig.get("skill_assessment_scores", {})
 
    skill_map = {sk["name"].lower(): sk for sk in skills}
    score = 0.0
 
    for t1 in TIER1_SKILLS:
        if t1 in skill_map:
            sk = skill_map[t1]
            pw = PROFICIENCY_WEIGHTS.get(sk.get("proficiency", "beginner"), 0.3)
            depth = min(sk.get("duration_months", 0) / 48.0, 0.25)
            assessment = 0.1 if assess.get(sk["name"], -1) >= 60 else 0.0
            score += pw + depth + assessment
 
    career_text = " ".join(
        j.get("description", "").lower() for j in c.get("career_history", [])
    )
    for t1 in TIER1_SKILLS:
        if t1 not in skill_map and t1 in career_text:
            score += 0.4
 
    disq = sum(
        1
        for sk in skills
        if sk["name"].lower() in DISQUALIFIER_SKILLS
        and sk.get("proficiency") in ("advanced", "expert")
        and sk.get("duration_months", 0) >= 24
    )
    disq_pen = max(0.3, 1.0 - disq * 0.15)
 
    return min(score / 10.0, 1.0) * disq_pen
 
 
def _career_score(c: dict) -> float:
    history = c.get("career_history", [])
    if not history:
        return 0.1
 
    total_months = sum(j.get("duration_months", 0) for j in history)
    product_months = 0
    score = 0.0
 
    for job in history:
        ind = job.get("industry", "").lower()
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        months = job.get("duration_months", 0)
        size = job.get("company_size", "")
 
        if any(pi in ind for pi in PRODUCT_INDUSTRIES):
            product_months += months
            score += 0.3
        if ind not in ("it services", "consulting"):
            score += 0.2
        if any(at in title for at in AI_TITLES):
            score += 0.4
        if size in ("11-50", "51-200", "201-500"):
            score += 0.2
        elif size in ("501-1000", "1001-5000"):
            score += 0.1
        term_hits = sum(1 for t in JD_TERMS if t in desc)
        score += min(term_hits * 0.15, 0.5)
 
    avg_tenure = total_months / len(history)
    if avg_tenure >= 24:
        score += 0.4
    elif avg_tenure >= 18:
        score += 0.2
 
    if total_months > 0:
        score += (product_months / total_months) * 0.5
 
    return min(score / 5.0, 1.0)
 
 
def _behavioral_score(c: dict) -> float:
    sig = c.get("redrob_signals", {})
    score = 0.0
 
    try:
        last = datetime.strptime(sig["last_active_date"], "%Y-%m-%d").date()
        days = (TODAY - last).days
    except Exception:
        days = 999
 
    if sig.get("open_to_work_flag"):
        score += 0.20
    if days <= 14:
        score += 0.20
    elif days <= 30:
        score += 0.15
    elif days <= 60:
        score += 0.10
    elif days <= 90:
        score += 0.05
 
    score += sig.get("recruiter_response_rate", 0) * 0.15
 
    notice = sig.get("notice_period_days", 90)
    if notice <= 30:
        score += 0.10
    elif notice <= 60:
        score += 0.07
    elif notice <= 90:
        score += 0.03
 
    gh = sig.get("github_activity_score", -1)
    if gh >= 60:
        score += 0.10
    elif gh >= 30:
        score += 0.06
    elif gh >= 10:
        score += 0.03
 
    score += (sig.get("profile_completeness_score", 0) / 100) * 0.06
    score += sig.get("interview_completion_rate", 0) * 0.06
 
    if sig.get("verified_email"):
        score += 0.02
    if sig.get("verified_phone"):
        score += 0.02
 
    score += min(sig.get("saved_by_recruiters_30d", 0) / 20, 1) * 0.04
 
    oar = sig.get("offer_acceptance_rate", -1)
    if oar >= 0:
        score += oar * 0.03
 
    if sig.get("linkedin_connected"):
        score += 0.02
 
    return min(score, 1.0)
 
 
def _experience_score(c: dict) -> float:
    yoe = c.get("profile", {}).get("years_of_experience", 0)
    history = c.get("career_history", [])
 
    research_titles = {
        "researcher", "research scientist", "phd", "postdoc", "academic",
    }
    all_research = bool(history) and all(
        any(rt in j.get("title", "").lower() for rt in research_titles)
        for j in history
    )
    research_pen = 0.3 if all_research else 1.0
 
    if 6.0 <= yoe <= 8.0:
        es = 1.0
    elif 5.0 <= yoe < 6.0 or 8.0 < yoe <= 9.0:
        es = 0.85
    elif 4.0 <= yoe < 5.0:
        es = 0.65
    elif 9.0 < yoe <= 12.0:
        es = 0.70
    elif yoe > 12.0:
        es = 0.50
    elif 3.0 <= yoe < 4.0:
        es = 0.40
    else:
        es = 0.15
 
    return es * research_pen
 
 
def _education_score(c: dict) -> float:
    score = 0.0
    for e in c.get("education", []):
        score += TIER_SCORES.get(e.get("tier", "unknown"), 0.4) * 0.5
        if any(f in e.get("field_of_study", "").lower() for f in CS_FIELDS):
            score += 0.3
        if any(
            d in e.get("degree", "").lower()
            for d in ["m.tech", "m.sc", "ms ", "msc", "phd", "mba", "m.e."]
        ):
            score += 0.2
    return min(score, 1.0)
 
 
def _location_score(c: dict) -> float:
    sig = c.get("redrob_signals", {})
    location = c.get("profile", {}).get("location", "").lower()
    country = c.get("profile", {}).get("country", "").lower()
 
    if any(city in location for city in PREFERRED_CITIES):
        return 1.0
    if "india" in country:
        return 0.8 if sig.get("willing_to_relocate") else 0.6
    return 0.3 if sig.get("willing_to_relocate") else 0.1
 
 
def _is_honeypot(c: dict) -> bool:
    yoe = c.get("profile", {}).get("years_of_experience", 0)
    skills = c.get("skills", [])
    history = c.get("career_history", [])
 
    for job in history:
        if job.get("duration_months", 0) > (yoe * 12 + 12):
            return True
 
    if sum(1 for s in skills if s.get("proficiency") == "expert") >= 10:
        return True
 
    total_months = sum(j.get("duration_months", 0) for j in history)
    if yoe > 2 and total_months < 6:
        return True
 
    for s in skills:
        if s.get("duration_months", 0) > (yoe * 12 * 1.5 + 12):
            return True
 
    return False
 
 
def _is_consulting_only(c: dict) -> bool:
    history = c.get("career_history", [])
    if not history:
        return False
    return all(
        any(cf in j.get("company", "").lower() for cf in CONSULTING_FIRMS)
        for j in history
    )
 
 
def build_reasoning(c: dict, matched: list, rank: int) -> str:
    p = c.get("profile", {})
    sig = c.get("redrob_signals", {})
 
    title = p.get("current_title", "Engineer")
    company = p.get("current_company", "")
    yoe = p.get("years_of_experience", 0)
    location = p.get("location", "")
 
    try:
        last = datetime.strptime(sig["last_active_date"], "%Y-%m-%d").date()
        days = (TODAY - last).days
        active_str = f"active {days}d ago" if days <= 30 else f"inactive {days}d"
    except Exception:
        active_str = "activity unknown"
 
    skills_str = ", ".join(matched[:4]) if matched else "general ML background"
    otw = "open to work; " if sig.get("open_to_work_flag") else ""
    rr = sig.get("recruiter_response_rate", 0)
    notice = sig.get("notice_period_days", 90)
 
    return (
        f"{title} at {company} ({yoe:.1f}yr); {skills_str}; "
        f"{otw}{active_str}; response {rr:.0%}; notice {notice}d; {location}"
    )
 
 
def get_text_for_embedding(c: dict) -> str:
    p = c.get("profile", {})
    skills = c.get("skills", [])
    history = c.get("career_history", [])
    certs = c.get("certifications", [])
 
    skill_str = " ".join(
        f"{s['name']} {s.get('proficiency','')} {s.get('duration_months',0)}mo"
        for s in sorted(skills, key=lambda x: -x.get("duration_months", 0))[:20]
    )
    career_str = " ".join(
        f"{j['title']} {j['company']} {j.get('description','')[:200]}"
        for j in history[:4]
    )
    cert_str = " ".join(cert.get("name", "") for cert in certs[:5])
 
    return (
        f"TITLE: {p.get('headline', '')} "
        f"SUMMARY: {p.get('summary', '')[:400]} "
        f"SKILLS: {skill_str} "
        f"CAREER: {career_str} "
        f"CERTS: {cert_str}"
    )
 

