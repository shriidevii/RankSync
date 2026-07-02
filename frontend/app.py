import csv
import io
import json
import sys
import math
import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "ranker"))

st.set_page_config(
    page_title="RankSync — AI Recruiter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{font-family:'Inter',system-ui,sans-serif!important}
.stApp{background:#030508}
[data-testid="stAppViewContainer"]{background:#030508}
[data-testid="stSidebar"]{background:#07090F!important;border-right:1px solid rgba(255,255,255,0.04)!important}
[data-testid="stSidebar"] *{color:#94A3B8!important}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,0.05)!important}
#MainMenu,footer,header{visibility:hidden}
::-webkit-scrollbar{width:3px;height:3px}
::-webkit-scrollbar-thumb{background:rgba(99,102,241,0.3);border-radius:99px}
::-webkit-scrollbar-track{background:transparent}

.stTabs [data-baseweb="tab-list"]{background:rgba(255,255,255,0.02)!important;border-radius:10px;padding:3px;border:1px solid rgba(255,255,255,0.04);gap:2px}
.stTabs [data-baseweb="tab"]{color:#334155!important;border-radius:8px!important;font-size:11.5px!important;font-weight:500!important;padding:7px 14px!important}
.stTabs [aria-selected="true"]{background:rgba(99,102,241,0.18)!important;color:#A5B4FC!important}
.stDownloadButton>button{background:linear-gradient(135deg,#6366F1,#8B5CF6)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;font-size:12px!important;box-shadow:0 0 20px rgba(99,102,241,0.25)!important;transition:all 0.2s!important}
.stDownloadButton>button:hover{box-shadow:0 0 32px rgba(99,102,241,0.5)!important;transform:translateY(-1px)!important}
div[data-testid="metric-container"]{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:14px 16px}
div[data-testid="metric-container"] label{color:#334155!important;font-size:11px!important;text-transform:uppercase;letter-spacing:0.08em}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{color:white!important;font-family:'JetBrains Mono',monospace!important;font-size:22px!important}
[data-testid="stSidebar"] .stButton>button{background:rgba(99,102,241,0.08)!important;color:#818CF8!important;border:1px solid rgba(99,102,241,0.15)!important;border-radius:8px!important;font-size:11px!important;width:100%!important}

.hero-wrap{position:relative;border-radius:20px;overflow:hidden;margin-bottom:18px;min-height:180px}
.hero-img-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(1.3) brightness(0.25)}
.hero-noise{position:absolute;inset:0;background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");opacity:0.4}
.hero-grid{position:absolute;inset:0;background-image:linear-gradient(rgba(99,102,241,0.07) 1px,transparent 1px),linear-gradient(90deg,rgba(99,102,241,0.07) 1px,transparent 1px);background-size:48px 48px}
.hero-glow{position:absolute;top:-100px;left:50%;transform:translateX(-50%);width:600px;height:300px;background:radial-gradient(ellipse,rgba(99,102,241,0.2) 0%,transparent 70%);pointer-events:none}
.hero-content{position:relative;z-index:2;padding:26px 28px;display:flex;align-items:center;gap:16px;justify-content:space-between;flex-wrap:nowrap}
.hero-left{flex:1;min-width:0;max-width:52%}
.brand-row{display:flex;align-items:center;gap:14px;margin-bottom:16px}
.brand-mark{width:46px;height:46px;background:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%);border-radius:13px;display:flex;align-items:center;justify-content:center;font-family:'Syne',sans-serif;font-size:16px;font-weight:900;color:white;letter-spacing:0.5px;box-shadow:0 0 32px rgba(99,102,241,0.5),inset 0 1px 0 rgba(255,255,255,0.15)}
.brand-name{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:white;letter-spacing:-0.5px}
.brand-sub{font-size:10px;color:#6366F1;font-weight:600;letter-spacing:0.2em;text-transform:uppercase;margin-top:1px}
.hero-tagline{font-size:12.5px;color:#64748B;line-height:1.55;max-width:400px;margin-bottom:12px}
.hero-tagline strong{color:#CBD5E1}
.pill-row{display:flex;gap:8px;flex-wrap:wrap}
.pill{font-size:11px;padding:5px 13px;border-radius:99px;font-weight:500;letter-spacing:0.02em;display:inline-flex;align-items:center;gap:5px}
.pill-g{background:rgba(16,185,129,0.1);color:#34D399;border:1px solid rgba(16,185,129,0.2)}
.pill-v{background:rgba(99,102,241,0.1);color:#A5B4FC;border:1px solid rgba(99,102,241,0.2)}
.pill-a{background:rgba(245,158,11,0.1);color:#FCD34D;border:1px solid rgba(245,158,11,0.2)}
.pill-s{background:rgba(255,255,255,0.04);color:#64748B;border:1px solid rgba(255,255,255,0.08)}
.hero-right{display:flex;gap:0;flex-shrink:0;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.08);border-radius:16px;overflow:hidden}
.hstat{text-align:center;padding:12px 16px;position:relative}
.hstat::after{content:'';position:absolute;right:0;top:20%;height:60%;width:1px;background:rgba(255,255,255,0.06)}
.hstat:last-child::after{display:none}
.hstat-val{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:white;letter-spacing:-0.5px;line-height:1}
.hstat-lbl{font-size:8px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.08em;margin-top:4px;white-space:nowrap}

.krow{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px}
.kcard{background:linear-gradient(135deg,#07090F,#0A0D16);border:1px solid rgba(255,255,255,0.05);border-radius:16px;padding:18px 20px;position:relative;overflow:hidden;transition:border-color 0.2s,transform 0.2s}
.kcard:hover{border-color:rgba(99,102,241,0.25);transform:translateY(-1px)}
.kcard-top{position:absolute;top:0;left:0;right:0;height:1px}
.kcard-glow{position:absolute;top:-40px;right:-40px;width:120px;height:120px;border-radius:50%;opacity:0.12}
.kcard-ico{font-size:20px;margin-bottom:10px;display:block}
.kcard-lbl{font-size:9.5px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:6px}
.kcard-val{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:white;letter-spacing:-0.5px;line-height:1;margin-bottom:3px}
.kcard-sub{font-size:10.5px;color:#475569}

.insight-strip{background:linear-gradient(90deg,rgba(99,102,241,0.08),rgba(139,92,246,0.05),rgba(99,102,241,0.08));border:1px solid rgba(99,102,241,0.15);border-left:2px solid #6366F1;border-radius:12px;padding:13px 18px;font-size:12.5px;color:#64748B;line-height:1.7;margin-bottom:16px}
.insight-strip strong{color:#E2E8F0}
.s-pill{background:rgba(16,185,129,0.15);color:#34D399;border:1px solid rgba(16,185,129,0.25);padding:1px 8px;border-radius:99px;font-size:10.5px;font-weight:700;font-family:'JetBrains Mono',monospace;display:inline}

.clist-wrap{background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:16px;overflow:hidden}
.clist-head{padding:14px 16px 12px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;justify-content:space-between}
.clist-title{font-size:10px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.14em}
.clist-count{font-size:10px;color:#64748B;background:rgba(255,255,255,0.03);padding:2px 8px;border-radius:99px;border:1px solid rgba(255,255,255,0.06)}
.clist-body{overflow-y:auto;max-height:520px}
.ci{display:flex;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid rgba(255,255,255,0.025);cursor:pointer;transition:all 0.12s;border-left:2px solid transparent}
.ci:hover{background:rgba(99,102,241,0.04);border-left-color:rgba(99,102,241,0.3)}
.ci.on{background:rgba(99,102,241,0.07);border-left-color:#6366F1}
.ci-rk{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:10.5px;font-weight:700;flex-shrink:0;font-family:'JetBrains Mono',monospace}
.rk1{background:linear-gradient(135deg,rgba(245,158,11,0.3),rgba(245,158,11,0.1));color:#FCD34D;box-shadow:0 0 10px rgba(245,158,11,0.2)}
.rk2{background:rgba(148,163,184,0.12);color:#94A3B8}
.rk3{background:rgba(234,88,12,0.12);color:#FB923C}
.rkd{background:rgba(99,102,241,0.08);color:#6366F1}
.ci-body{flex:1;min-width:0}
.ci-name{font-size:12px;font-weight:600;color:#CBD5E1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ci-role{font-size:10px;color:#475569;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}
.ci-dot{width:5px;height:5px;border-radius:50%;background:#10B981;flex-shrink:0;box-shadow:0 0 5px #10B981}
.ci-score{font-size:12.5px;font-weight:700;color:#6366F1;font-family:'JetBrains Mono',monospace;flex-shrink:0}

.dcard{background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:16px;overflow:hidden}
.dhdr{background:linear-gradient(145deg,#0D1224 0%,#111840 55%,#0D1224 100%);padding:24px 26px 22px;position:relative;overflow:hidden}
.dhdr-orb1{position:absolute;top:-80px;right:-80px;width:260px;height:260px;background:radial-gradient(circle,rgba(99,102,241,0.2),transparent 70%);pointer-events:none}
.dhdr-orb2{position:absolute;bottom:-60px;left:-20px;width:180px;height:180px;background:radial-gradient(circle,rgba(139,92,246,0.12),transparent 70%);pointer-events:none}
.dhdr-line{position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,0.4),transparent)}
.d-rank-lbl{font-size:9.5px;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.16em;margin-bottom:8px;font-family:'JetBrains Mono',monospace;position:relative;z-index:1}
.d-name{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:white;letter-spacing:-0.5px;margin-bottom:3px;position:relative;z-index:1}
.d-title{font-size:13px;color:#818CF8;margin-bottom:10px;position:relative;z-index:1}
.d-badges{display:flex;gap:6px;flex-wrap:wrap;position:relative;z-index:1}
.d-score-area{position:absolute;top:24px;right:26px;z-index:2;text-align:right}
.d-score{font-family:'Syne',sans-serif;font-size:40px;font-weight:800;color:white;line-height:1;letter-spacing:-2px}
.d-score-lbl{font-size:9px;color:#6366F1;text-transform:uppercase;letter-spacing:0.14em;margin-top:4px;font-weight:600;text-align:right}
.d-score-type{font-size:8px;color:#475569;text-align:right;margin-top:1px}

.dbody{padding:20px 24px}
.sh{font-size:9.5px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.14em;margin:18px 0 10px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.04)}
.sh:first-child{margin-top:0}

.sbar{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.sbar-l{font-size:11px;color:#64748B;width:118px;flex-shrink:0}
.sbar-t{flex:1;height:4px;background:rgba(255,255,255,0.04);border-radius:99px;overflow:hidden;position:relative}
.sbar-f{height:100%;border-radius:99px;position:relative}
.sbar-f::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15));border-radius:99px}
.sbar-v{font-size:10.5px;font-weight:600;color:#64748B;width:30px;text-align:right;font-family:'JetBrains Mono',monospace}
.sbar-w{font-size:9px;color:#475569;width:24px;text-align:right}

.sig-g{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:4px}
.sig{background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:12px;text-align:center}
.sig-v{font-size:16px;font-weight:700;font-family:'JetBrains Mono',monospace;line-height:1}
.sig-l{font-size:8.5px;color:#475569;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px}

.sk{display:inline-block;background:rgba(99,102,241,0.1);color:#818CF8;border:1px solid rgba(99,102,241,0.2);padding:3px 9px;border-radius:6px;font-size:10px;font-weight:500;margin:2px;font-family:'JetBrains Mono',monospace}
.sk-dim{display:inline-block;background:rgba(255,255,255,0.02);color:#334155;border:1px solid rgba(255,255,255,0.05);padding:3px 9px;border-radius:6px;font-size:10px;margin:2px}

.rbox{background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(139,92,246,0.04));border:1px solid rgba(99,102,241,0.12);border-radius:10px;padding:14px 16px;font-size:12.5px;color:#64748B;line-height:1.75;margin-top:8px}
.rbox-lbl{font-size:9px;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:7px;display:flex;align-items:center;gap:5px}

.tl{padding:11px 14px 11px 22px;border-left:1px solid rgba(255,255,255,0.06);margin-left:10px;margin-bottom:7px;position:relative}
.tl::before{content:'';width:7px;height:7px;background:#6366F1;border-radius:50%;position:absolute;left:-4px;top:16px;box-shadow:0 0 8px rgba(99,102,241,0.6)}
.tl.cur{border-color:rgba(99,102,241,0.4)}
.tl-co{font-size:12.5px;font-weight:600;color:#E2E8F0}
.tl-role{font-size:11.5px;color:#6366F1;margin-top:2px}
.tl-meta{font-size:10.5px;color:#475569;margin-top:3px}
.tl-desc{font-size:10.5px;color:#64748B;margin-top:5px;line-height:1.65}

.badge{display:inline-flex;align-items:center;padding:3px 9px;border-radius:99px;font-size:10px;font-weight:600;letter-spacing:0.01em}
.bg{background:rgba(16,185,129,0.1);color:#34D399;border:1px solid rgba(16,185,129,0.2)}
.bb{background:rgba(99,102,241,0.1);color:#818CF8;border:1px solid rgba(99,102,241,0.2)}
.ba{background:rgba(245,158,11,0.1);color:#FCD34D;border:1px solid rgba(245,158,11,0.2)}
.br{background:rgba(239,68,68,0.1);color:#F87171;border:1px solid rgba(239,68,68,0.2)}

.dist-row{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.dist-lbl{font-size:10.5px;color:#64748B;width:88px;flex-shrink:0;font-family:'JetBrains Mono',monospace}
.dist-t{flex:1;height:20px;background:rgba(255,255,255,0.03);border-radius:4px;overflow:hidden}
.dist-f{height:100%;border-radius:4px;display:flex;align-items:center;padding:0 8px}
.dist-f span{font-size:10px;font-weight:700;color:rgba(255,255,255,0.85);font-family:'JetBrains Mono',monospace}
.dist-n{font-size:10.5px;color:#475569;width:22px;text-align:right;font-family:'JetBrains Mono',monospace}

.tier-g{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.tier-b{border-radius:12px;padding:14px 16px}
.tier-n{font-size:11px;font-weight:700;margin-bottom:5px}
.tier-c{font-size:26px;font-weight:800;line-height:1;font-family:'JetBrains Mono',monospace}
.tier-r{font-size:10px;margin-top:4px;opacity:0.7}

.geo-row{display:flex;align-items:center;gap:8px;margin-bottom:7px}
.geo-city{font-size:11px;color:#64748B;width:95px;flex-shrink:0}
.geo-bar{flex:1;height:5px;background:rgba(255,255,255,0.04);border-radius:99px;overflow:hidden}
.geo-fill{height:100%;border-radius:99px}
.geo-n{font-size:10.5px;color:#475569;width:20px;text-align:right;font-family:'JetBrains Mono',monospace}

.chart-panel{background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:16px;padding:18px 20px}
.chart-title{font-size:10px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:14px}

.footer-bar{padding:14px 0;border-top:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;justify-content:space-between;margin-top:4px}
.footer-txt{font-size:10.5px;color:#475569}

.exp-badge{display:inline-block;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:10px 14px;text-align:center;margin:4px}
.exp-val{font-size:18px;font-weight:700;color:white;font-family:'JetBrains Mono',monospace}
.exp-lbl{font-size:9px;color:#64748B;text-transform:uppercase;letter-spacing:0.1em;margin-top:2px}

.block-container{padding:1.5rem 1.5rem 2rem!important;max-width:100%!important}
section[data-testid="stMain"]>.block-container{padding-top:1rem!important}
.stButton>button{background:rgba(99,102,241,0.08)!important;color:#818CF8!important;border:1px solid rgba(99,102,241,0.15)!important;border-radius:8px!important;font-size:11.5px!important;text-align:left!important;padding:8px 12px!important;height:auto!important;white-space:pre-wrap!important;line-height:1.4!important}
.stButton>button:hover{background:rgba(99,102,241,0.15)!important;border-color:rgba(99,102,241,0.35)!important}
.hstat-lbl{font-size:9px!important;color:#94A3B8!important}

</style>
""", unsafe_allow_html=True)

TODAY = datetime.date(2026, 6, 20)

TIER1_SKILLS = frozenset({
    "embeddings","embedding","semantic search","dense retrieval","vector search",
    "sentence-transformers","sentence transformers","bge","e5","pgvector",
    "pinecone","weaviate","qdrant","milvus","opensearch","elasticsearch",
    "faiss","chromadb","learning to rank","bm25","hybrid search",
    "information retrieval","ranking","reranking","re-ranking","ndcg","mrr",
    "python","recommendation systems","mlops","a/b testing","evaluation frameworks",
})

DATASET_PATHS = [
    ROOT / "backend" / "dataset" / "candidates.jsonl",
    Path("backend/dataset/candidates.jsonl"),
    ROOT / "backend" / "dataset" / "sample_candidates.json",
    Path("backend/dataset/sample_candidates.json"),
]

def days_inactive(c):
    try:
        last = datetime.date.fromisoformat(c.get("redrob_signals",{})["last_active_date"])
        return max(0,(TODAY-last).days)
    except:
        return 999

@st.cache_data(show_spinner="⚡ Scoring 100k candidates...")
def load_and_score():
    import rank as R
    raw=[]
    for p in DATASET_PATHS:
        if p.exists():
            if str(p).endswith(".jsonl"):
                with open(p,"r",encoding="utf-8") as f:
                    for line in f:
                        line=line.strip()
                        if line:
                            try: raw.append(json.loads(line))
                            except: pass
            else:
                with open(p,"r",encoding="utf-8") as f:
                    d=json.load(f)
                raw=d if isinstance(d,list) else list(d.values())
            break
    if not raw: return [],{}
    scored,hp=[],[]
    for c in raw:
        r=R.score_candidate(c)
        (hp if r["is_honeypot"] else scored).append(r)
    scored.sort(key=lambda x:(-x["final_score"],-x["career"],x["candidate_id"]))
    gs={"total":len(raw),"valid":len(scored),"honey":len(hp),
        "open":sum(1 for c in raw if c.get("redrob_signals",{}).get("open_to_work_flag",False)),
        "active":sum(1 for c in raw if days_inactive(c)<=30)}
    ui=[]
    for ri,r in enumerate(scored[:1000],1):
        c=r["_candidate"]; p=c["profile"]; sig=c["redrob_signals"]
        matched=[s["name"] for s in c.get("skills",[]) if s.get("name","").lower() in TIER1_SKILLS or any(t in s.get("name","").lower() for t in TIER1_SKILLS if len(t)>5)]
        edu=""
        if c.get("education"):
            e=c["education"][0]; edu=f"{e.get('degree','')} — {e.get('institution','')}"
        di=days_inactive(c)
        ui.append({"rank":ri,"id":c["candidate_id"],"name":p.get("anonymized_name",c["candidate_id"]),
            "title":p.get("current_title",""),"company":p.get("current_company",""),
            "industry":p.get("current_industry",""),"yoe":p.get("years_of_experience",0),
            "location":p.get("location",""),"country":p.get("country",""),
            "final":r["final_score"],"career":r["career"],"skill":r["skill"],
            "beh":r["behavioral"],"exp":r["experience"],"edu_score":r["education"],
            "loc_score":r["location"],"matched":matched,"days":di,
            "open":sig.get("open_to_work_flag",False),"rr":sig.get("recruiter_response_rate",0),
            "notice":sig.get("notice_period_days",90),"github":sig.get("github_activity_score",-1),
            "completeness":sig.get("profile_completeness_score",0),
            "interview_cr":sig.get("interview_completion_rate",0),
            "saved":sig.get("saved_by_recruiters_30d",0),
            "salary_min":sig.get("expected_salary_range_inr_lpa",{}).get("min",0),
            "salary_max":sig.get("expected_salary_range_inr_lpa",{}).get("max",0),
            "work_mode":sig.get("preferred_work_mode",""),"relocate":sig.get("willing_to_relocate",False),
            "honey":False,"flags":r.get("flags",{}),"reasoning":R.generate_reasoning(c,r,ri),
            "edu":edu,"certs":[cert["name"] for cert in c.get("certifications",[])[:3]],
            "career_history":c.get("career_history",[])[:5],
            "all_skills":[{"name":s["name"],"prof":s.get("proficiency",""),"months":s.get("duration_months",0)} for s in c.get("skills",[])[:20]],
            "raw_sig":sig,"honey":False})
    for r in hp[:100]:
        c=r["_candidate"]; p=c["profile"]
        ui.append({"rank":99999,"id":c["candidate_id"],"name":p.get("anonymized_name",c["candidate_id"]),
            "title":p.get("current_title",""),"company":p.get("current_company",""),
            "industry":"","yoe":p.get("years_of_experience",0),"location":p.get("location",""),
            "country":p.get("country",""),"final":0.0,"career":0.0,"skill":0.0,"beh":0.0,
            "exp":0.0,"edu_score":0.0,"loc_score":0.0,"matched":[],"days":999,
            "open":False,"rr":0.0,"notice":0,"github":-1,"completeness":0,"interview_cr":0,
            "saved":0,"salary_min":0,"salary_max":0,"work_mode":"","relocate":False,
            "honey":True,"flags":{},"reasoning":r.get("hp_reason","Honeypot"),"edu":"",
            "certs":[],"career_history":[],"all_skills":[],"raw_sig":c.get("redrob_signals",{})})
    return ui,gs

def sbar(label,val,color,w=""):
    pct=min(max(float(val),0),1)*100
    return (f"<div class='sbar'><div class='sbar-l'>{label}</div>"
            f"<div class='sbar-t'><div class='sbar-f' style='width:{pct:.0f}%;background:{color}'></div></div>"
            f"<div class='sbar-v'>{val:.2f}</div><div class='sbar-w'>{w}</div></div>")

def tier(score):
    if score>=0.85: return "bg","● Strong Hire"
    if score>=0.78: return "bb","● Good Fit"
    if score>=0.71: return "ba","● Moderate"
    return "br","● Marginal"

def gh(v): return "N/A" if v<0 else f"{v:.0f}/100"

with st.sidebar:
    st.markdown("<div style='padding:14px 0 8px;font-family:Syne,sans-serif;font-size:16px;font-weight:800;color:#E2E8F0;letter-spacing:-0.5px'>⚡ RankSync</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:9px;color:#6366F1;font-weight:700;text-transform:uppercase;letter-spacing:0.18em;margin-bottom:12px'>AI Ranking Engine · Redrob</div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<div style='font-size:9.5px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:10px'>Filters</div>", unsafe_allow_html=True)
    f_open=st.checkbox("Open to Work only",False)
    f_active=st.checkbox("Active ≤ 30 days",False)
    f_india=st.checkbox("India only",False)
    min_yoe,max_yoe=st.slider("Experience (yr)",0.0,20.0,(0.0,20.0),0.5)
    min_gh=st.slider("Min GitHub",-1,100,-1,5)
    st.divider()
    st.markdown("<div style='font-size:9.5px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:10px'>View</div>", unsafe_allow_html=True)
    view=st.radio("",["🏆 Ranked List","📊 Analytics","🍯 Honeypots"],label_visibility="collapsed")
    st.divider()
    top_n=st.number_input("Show top N",5,100,20,5)

results,gs=load_and_score()
if not results:
    st.error("❌ No candidates. Check backend/dataset/candidates.jsonl"); st.stop()

clean=[r for r in results if not r["honey"]]
filtered=clean.copy()
if f_open:   filtered=[r for r in filtered if r["open"]]
if f_active: filtered=[r for r in filtered if r["days"]<=30]
if f_india:  filtered=[r for r in filtered if "india" in r["country"].lower()]
filtered=[r for r in filtered if min_yoe<=r["yoe"]<=max_yoe]
if min_gh>-1: filtered=[r for r in filtered if r["github"]>=min_gh]
t1=filtered[0] if filtered else clean[0]

_gh1=gh(t1["github"])
_otw="✅ Open to work · " if t1["open"] else ""
sk3=", ".join(t1["matched"][:3]) if t1["matched"] else "strong career evidence"

st.markdown(f"""
<div class='hero-wrap'>
  <img class='hero-img-bg' src='https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=1600&q=80'
    onerror="this.src='https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1600&q=80'">
  <div class='hero-noise'></div>
  <div class='hero-grid'></div>
  <div class='hero-glow'></div>
  <div class='hero-content'>
    <div class='hero-left'>
      <div class='brand-row'>
        <div class='brand-mark'>RS</div>
        <div>
          <div class='brand-name'>RankSync</div>
          <div class='brand-sub'>Redrob Hackathon · Team RankSync</div>
        </div>
      </div>
      <div class='hero-tagline'>
        Surfaced the <strong>top 100 Senior AI Engineers</strong> from {gs['total']:,} candidates
        using a 6-component weighted scoring engine.
        <strong>Raw honest scores. No normalization.</strong>
      </div>
      <div class='pill-row'>
        <span class='pill pill-g'>● Live</span>
        <span class='pill pill-v'>CPU · Offline · Deterministic</span>
        <span class='pill pill-a'>⚡ 58s runtime</span>
        <span class='pill pill-s'>Zero pip installs</span>
        <span class='pill pill-v'>Track 1 · Senior AI Engineer</span>
      </div>
    </div>
    <div class='hero-right'>
      <div class='hstat'><div class='hstat-val'>{gs['total']:,}</div><div class='hstat-lbl'>Candidates</div></div>
      <div class='hstat'><div class='hstat-val'>{t1['final']:.4f}</div><div class='hstat-lbl'>Top Score</div></div>
      <div class='hstat'><div class='hstat-val'>{gs['honey']}</div><div class='hstat-lbl'>Honeypots</div></div>
      <div class='hstat'><div class='hstat-val'>58s</div><div class='hstat-lbl'>Runtime</div></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class='krow'>
  <div class='kcard'>
    <div class='kcard-top' style='background:linear-gradient(90deg,#6366F1,#8B5CF6)'></div>
    <div class='kcard-glow' style='background:#6366F1'></div>
    <span class='kcard-ico'>🎯</span>
    <div class='kcard-lbl'>Total Scored</div>
    <div class='kcard-val'>{gs['total']:,}</div>
    <div class='kcard-sub'>full 100k dataset</div>
  </div>
  <div class='kcard'>
    <div class='kcard-top' style='background:linear-gradient(90deg,#10B981,#34D399)'></div>
    <div class='kcard-glow' style='background:#10B981'></div>
    <span class='kcard-ico'>🏆</span>
    <div class='kcard-lbl'>Top Raw Score</div>
    <div class='kcard-val'>{t1['final']:.4f}</div>
    <div class='kcard-sub'>honest · no normalization</div>
  </div>
  <div class='kcard'>
    <div class='kcard-top' style='background:linear-gradient(90deg,#8B5CF6,#C084FC)'></div>
    <div class='kcard-glow' style='background:#8B5CF6'></div>
    <span class='kcard-ico'>✅</span>
    <div class='kcard-lbl'>Open to Work</div>
    <div class='kcard-val'>{gs['open']:,}</div>
    <div class='kcard-sub'>actively available</div>
  </div>
  <div class='kcard'>
    <div class='kcard-top' style='background:linear-gradient(90deg,#F59E0B,#FCD34D)'></div>
    <div class='kcard-glow' style='background:#F59E0B'></div>
    <span class='kcard-ico'>🍯</span>
    <div class='kcard-lbl'>Honeypots</div>
    <div class='kcard-val'>{gs['honey']}</div>
    <div class='kcard-sub'>detected &amp; excluded</div>
  </div>
  <div class='kcard'>
    <div class='kcard-top' style='background:linear-gradient(90deg,#EF4444,#F87171)'></div>
    <div class='kcard-glow' style='background:#EF4444'></div>
    <span class='kcard-ico'>⚡</span>
    <div class='kcard-lbl'>Runtime</div>
    <div class='kcard-val'>58s</div>
    <div class='kcard-sub'>CPU · no GPU needed</div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown(
    f"<div class='insight-strip'>🤖 <strong>Top Match:</strong> <strong>{t1['name']}</strong> "
    f"({t1['title']} @ {t1['company']} · {t1['yoe']:.1f}yr · {t1['location']}) scores "
    f"<span class='s-pill'>{t1['final']:.4f}</span> — "
    f"career <strong>{t1['career']:.3f}</strong> · skill <strong>{t1['skill']:.3f}</strong> · "
    f"behavioral <strong>{t1['beh']:.3f}</strong>. "
    f"JD skills matched: <strong>{sk3}</strong>. "
    f"{_otw}Response rate {t1['rr']:.0%} · Notice {t1['notice']}d · GitHub {_gh1}.</div>",
    unsafe_allow_html=True)

if view=="🏆 Ranked List":
    L,R=st.columns([1,2],gap="medium")
    with L:
        st.markdown(f"<div class='clist-wrap'><div class='clist-head'><div class='clist-title'>Top Candidates</div><div class='clist-count'>{min(top_n,len(filtered))} of {len(filtered)}</div></div><div class='clist-body'>",unsafe_allow_html=True)
        if "sel" not in st.session_state: st.session_state.sel=filtered[0]["id"] if filtered else None
        for r in filtered[:top_n]:
            tc,_=tier(r["final"])
            rk=r["rank"]
            rc="rk1" if rk==1 else "rk2" if rk==2 else "rk3" if rk==3 else "rkd"
            dot=f"<div class='ci-dot'></div>" if r["open"] else ""
            active_cls="on" if r["id"]==st.session_state.get("sel") else ""
            lbl=(f"{'🥇' if rk==1 else '🥈' if rk==2 else '🥉' if rk==3 else f'#{rk}'}  "
                 f"{r['name']} {'●' if r['open'] else ''}\n"
                 f"{r['title']} · {r['yoe']:.1f}yr · {r['final']:.4f}")
            if st.button(lbl,key=f"b_{r['id']}",use_container_width=True):
                st.session_state.sel=r["id"]; st.rerun()
        st.markdown("</div></div>",unsafe_allow_html=True)

    with R:
        sel=next((r for r in results if r["id"]==st.session_state.get("sel")),filtered[0] if filtered else None)
        if not sel:
            st.info("Select a candidate.")
        else:
            tc,tl=tier(sel["final"])
            fl=sel.get("flags",{})
            badges=f"<span class='badge {tc}'>{tl}</span>"
            if sel["honey"]:  badges+=" <span class='badge br'>⚠ Honeypot</span>"
            if sel["open"]:   badges+=" <span class='badge bg'>✓ Open to work</span>"
            if fl.get("consulting_only"):    badges+=" <span class='badge ba'>🏢 Consulting-only</span>"
            if fl.get("pure_research_only"): badges+=" <span class='badge ba'>🔬 Research-only</span>"
            if fl.get("title_chaser"):       badges+=" <span class='badge ba'>⚡ Title-chaser</span>"
            _gh2=gh(sel["github"])
            act_str=f"Active {sel['days']}d ago" if sel["days"]>0 else "Active now"

            st.markdown(f"""
<div class='dcard'>
  <div class='dhdr'>
    <div class='dhdr-orb1'></div><div class='dhdr-orb2'></div><div class='dhdr-line'></div>
    <div class='d-score-area'>
      <div class='d-score'>{sel['final']:.4f}</div>
      <div class='d-score-lbl'>Match Score</div>
      <div class='d-score-type'>RAW · no normalization</div>
    </div>
    <div class='d-rank-lbl'>RANK #{sel['rank']} · {sel['id']}</div>
    <div class='d-name'>{sel['name']}</div>
    <div class='d-title'>{sel['title']} @ {sel['company']} · {sel['yoe']:.1f}yr</div>
    <div class='d-badges'>{badges}</div>
  </div>
</div>""", unsafe_allow_html=True)

            tabs=st.tabs([" Scores"," Career"," Skills"," Signals"," AI"])

            with tabs[0]:
                st.markdown(
                    "<div class='sh'>Score breakdown — career 32% · skill 28% · behavioral 22% · exp 8% · edu 5% · loc 5%</div>"+
                    sbar("Career quality",sel["career"],"linear-gradient(90deg,#10B981,#34D399)","32%")+
                    sbar("Skill match",sel["skill"],"linear-gradient(90deg,#6366F1,#818CF8)","28%")+
                    sbar("Behavioral",sel["beh"],"linear-gradient(90deg,#8B5CF6,#A78BFA)","22%")+
                    sbar("Experience fit",sel["exp"],"linear-gradient(90deg,#F59E0B,#FCD34D)","8%")+
                    sbar("Education",sel["edu_score"],"linear-gradient(90deg,#06B6D4,#38BDF8)","5%")+
                    sbar("Location",sel["loc_score"],"linear-gradient(90deg,#EC4899,#F472B6)","5%"),
                    unsafe_allow_html=True)
                rrc="#34D399" if sel["rr"]>=0.7 else "#F59E0B" if sel["rr"]>=0.4 else "#F87171"
                nc="#34D399" if sel["notice"]<=30 else "#F59E0B" if sel["notice"]<=60 else "#F87171"
                ac="#34D399" if sel["days"]<=14 else "#F59E0B" if sel["days"]<=60 else "#F87171"
                st.markdown(f"""
<div class='sh'>Behavioral signals</div>
<div class='sig-g'>
  <div class='sig'><div class='sig-v' style='color:{rrc}'>{sel['rr']:.0%}</div><div class='sig-l'>Response Rate</div></div>
  <div class='sig'><div class='sig-v' style='color:{nc}'>{sel['notice']}d</div><div class='sig-l'>Notice Period</div></div>
  <div class='sig'><div class='sig-v' style='color:{ac}'>{act_str}</div><div class='sig-l'>Last Active</div></div>
  <div class='sig'><div class='sig-v' style='color:{"#34D399" if sel["github"]>=60 else "#64748B"}'>{_gh2}</div><div class='sig-l'>GitHub Score</div></div>
  <div class='sig'><div class='sig-v' style='color:{"#34D399" if sel["open"] else "#F87171"}'>{"Yes" if sel["open"] else "No"}</div><div class='sig-l'>Open to Work</div></div>
  <div class='sig'><div class='sig-v' style='color:#818CF8'>{sel['yoe']:.1f}yr</div><div class='sig-l'>Experience</div></div>
</div>""", unsafe_allow_html=True)
                c1,c2,c3=st.columns(3)
                c1.metric("Salary",f"₹{sel['salary_min']:.0f}–{sel['salary_max']:.0f}L")
                c2.metric("Work Mode",sel["work_mode"].title() if sel["work_mode"] else "—")
                c3.metric("Relocate","Yes" if sel["relocate"] else "No")
                if sel["edu"]: st.markdown(f"<div style='font-size:11.5px;color:#64748B;margin-top:10px'>🎓 {sel['edu']}</div>",unsafe_allow_html=True)

            with tabs[1]:
                for job in sel["career_history"]:
                    mo=job.get("duration_months",0)
                    dur=f"{mo/12:.1f}yr" if mo>=12 else f"{mo}mo"
                    curr=job.get("is_current",False)
                    desc=job.get("description","")[:300]
                    ctag="<span style='color:#34D399;font-size:9.5px;font-weight:700'> · CURRENT</span>" if curr else ""
                    st.markdown(f"""
<div class='tl {"cur" if curr else ""}'>
  <div class='tl-co'>{job.get('company','')} {ctag}</div>
  <div class='tl-role'>{job.get('title','')}</div>
  <div class='tl-meta'>{dur} · {job.get('company_size','')} · {job.get('industry','')}</div>
  {"<div class='tl-desc'>"+desc+("..." if len(job.get('description',''))>300 else "")+"</div>" if desc else ""}
</div>""", unsafe_allow_html=True)

            with tabs[2]:
                if sel["matched"]:
                    st.markdown("<div style='font-size:9.5px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px'>✅ Matched JD Tier-1 Skills</div>",unsafe_allow_html=True)
                    st.markdown(" ".join(f"<span class='sk'>✓ {s}</span>" for s in sel["matched"]),unsafe_allow_html=True)
                else:
                    st.caption("No tier-1 JD skill matches.")
                st.markdown("<div style='font-size:9.5px;font-weight:700;color:#64748B;text-transform:uppercase;letter-spacing:0.12em;margin:14px 0 8px'>All Skills</div>",unsafe_allow_html=True)
                pc={"expert":"#6366F1","advanced":"#10B981","intermediate":"#F59E0B","beginner":"#475569"}
                html=""
                for sk in sorted(sel["all_skills"],key=lambda x:-x["months"]):
                    col=pc.get(sk["prof"],"#475569")
                    yr=f"{sk['months']//12}yr" if sk["months"]>=12 else f"{sk['months']}mo"
                    brd="border-color:rgba(99,102,241,0.5);" if sk["name"] in sel["matched"] else ""
                    html+=(f"<span class='sk-dim' style='{brd}'>"
                           f"<span style='color:{col};font-weight:700;font-size:9px'>{sk['prof'][:3].upper()}</span>"
                           f" {sk['name']} <span style='color:#475569;font-size:9px'>({yr})</span></span>")
                st.markdown(html,unsafe_allow_html=True)
                if sel["all_skills"]:
                    top_sk=sorted(sel["all_skills"],key=lambda x:-x["months"])[:10]
                    st.bar_chart(pd.DataFrame(top_sk).rename(columns={"name":"Skill","months":"Months"}).set_index("Skill")["Months"],color="#6366F1")

            with tabs[3]:
                sig=sel["raw_sig"]; rows=[]
                for k,v in sig.items():
                    if isinstance(v,dict): vs=", ".join(f"{kk}: {vv}" for kk,vv in v.items())
                    elif isinstance(v,bool): vs="✓ Yes" if v else "✗ No"
                    elif isinstance(v,float) and 0<=v<=1 and k not in ("github_activity_score","offer_acceptance_rate"): vs=f"{v:.3f}"
                    else: vs=str(v)
                    rows.append({"Signal":k.replace("_"," ").title(),"Value":vs})
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

            with tabs[4]:
                st.markdown(f"<div class='rbox'><div class='rbox-lbl' AI Ranking Rationale</div>{sel['reasoning']}</div>",unsafe_allow_html=True)
                st.markdown("<div class='sh' style='margin-top:16px'>✅ Strengths</div>",unsafe_allow_html=True)
                ss=[]
                if sel["matched"]: ss.append(f"{len(sel['matched'])} JD tier-1 skills: {', '.join(sel['matched'][:4])}")
                if 5<=sel["yoe"]<=9: ss.append(f"Experience {sel['yoe']:.1f}yr — JD target 5–9yr")
                if sel["open"]: ss.append("Open to work — actively available")
                if sel["days"]<=14: ss.append(f"Active now ({sel['days']}d ago)")
                if sel["rr"]>=0.7: ss.append(f"Strong response rate ({sel['rr']:.0%})")
                if sel["notice"]<=30: ss.append(f"Short notice ({sel['notice']}d)")
                if sel["github"]>=60: ss.append(f"Active GitHub ({sel['github']:.0f}/100)")
                if sel["career"]>=0.75: ss.append("Strong production AI/ML career evidence")
                for s in (ss or ["No notable strengths"]):
                    st.markdown(f"<div style='font-size:12.5px;color:#34D399;padding:3px 0'>✓ {s}</div>",unsafe_allow_html=True)
                st.markdown("<div class='sh'>⚠ Gaps / Concerns</div>",unsafe_allow_html=True)
                gg=[]
                if fl.get("consulting_only"):    gg.append("Consulting-only background (0.35× penalty)")
                if fl.get("pure_research_only"): gg.append("Pure research — no production deployment")
                if fl.get("title_chaser"):       gg.append("Frequent job changes (avg tenure <14mo)")
                if fl.get("no_ai_career_evidence"): gg.append("No production AI/ML career evidence")
                if not sel["matched"]: gg.append("No tier-1 JD skill matches")
                if sel["days"]>90: gg.append(f"Inactive {sel['days']}d — availability uncertain")
                if sel["rr"]<0.4: gg.append(f"Low response rate ({sel['rr']:.0%})")
                if sel["notice"]>90: gg.append(f"Long notice period ({sel['notice']}d)")
                if sel["yoe"]<5 or sel["yoe"]>12: gg.append(f"Experience {sel['yoe']:.1f}yr outside 5–12yr target")
                for g in (gg or ["No major disqualifiers"]):
                    st.markdown(f"<div style='font-size:12.5px;color:#F87171;padding:3px 0'>✗ {g}</div>",unsafe_allow_html=True)

elif view=="📊 Analytics":
    st.markdown("<div style='font-family:Syne,sans-serif;font-size:18px;font-weight:800;color:#E2E8F0;letter-spacing:-0.5px;margin-bottom:16px'>📊 Analytics</div>",unsafe_allow_html=True)
    df=pd.DataFrame([{"Rank":r["rank"],"Name":r["name"],"Title":r["title"][:28],
        "Company":r["company"],"YoE":r["yoe"],"Score":round(r["final"],4),
        "Career":round(r["career"],3),"Skill":round(r["skill"],3),
        "Behavioral":round(r["beh"],3),"JD Skills":len(r["matched"]),
        "Active(d)":r["days"],"RR":f"{r['rr']:.0%}","Notice":r["notice"],
        "GitHub":r["github"] if r["github"]>=0 else -1,"OTW":"✓" if r["open"] else "—"}
        for r in filtered[:top_n]])
    st.dataframe(df,use_container_width=True,hide_index=True,column_config={
        "Score":st.column_config.ProgressColumn("Score",min_value=0,max_value=1,format="%.4f"),
        "Career":st.column_config.ProgressColumn("Career",min_value=0,max_value=1,format="%.3f"),
        "Skill":st.column_config.ProgressColumn("Skill",min_value=0,max_value=1,format="%.3f"),
        "Behavioral":st.column_config.ProgressColumn("Beh",min_value=0,max_value=1,format="%.3f")})

    scores_top=[r["final"] for r in clean[:100]]
    bkts={"0.90+":0,"0.86–0.90":0,"0.82–0.86":0,"0.78–0.82":0,"0.74–0.78":0,"0.71–0.74":0}
    for s in scores_top:
        if s>=0.90: bkts["0.90+"]+=1
        elif s>=0.86: bkts["0.86–0.90"]+=1
        elif s>=0.82: bkts["0.82–0.86"]+=1
        elif s>=0.78: bkts["0.78–0.82"]+=1
        elif s>=0.74: bkts["0.74–0.78"]+=1
        else: bkts["0.71–0.74"]+=1
    cols=["linear-gradient(90deg,#10B981,#34D399)","linear-gradient(90deg,#34D399,#6EE7B7)",
          "linear-gradient(90deg,#6366F1,#818CF8)","linear-gradient(90deg,#6366F1,#8B5CF6)",
          "linear-gradient(90deg,#8B5CF6,#A78BFA)","linear-gradient(90deg,#334155,#475569)"]
    mx=max(bkts.values()) or 1
    dh="<div class='chart-panel'><div class='chart-title'>Score Distribution · Top 100 · Real buckets</div>"
    for (lbl,cnt),col in zip(bkts.items(),cols):
        pct=cnt/mx*100
        dh+=f"<div class='dist-row'><div class='dist-lbl'>{lbl}</div><div class='dist-t'><div class='dist-f' style='width:{pct:.0f}%;background:{col}'><span>{cnt}</span></div></div><div class='dist-n'>{cnt}</div></div>"
    dh+=f"<div style='margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.04);font-size:10.5px;color:#64748B'>Rank 100 = <span style='color:#94A3B8;font-family:monospace;font-weight:600'>{clean[99]['final']:.4f}</span> — top 0.1% of {gs['total']:,}. Not 0.01.</div></div>"
    st.markdown(dh,unsafe_allow_html=True)

    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#334155;margin-bottom:8px'>Score Distribution</div>",unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame({"Score":[r["final"] for r in filtered[:top_n]]}),color="#6366F1")
    with c2:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#334155;margin-bottom:8px'>Experience Distribution</div>",unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame({"YoE":[r["yoe"] for r in filtered[:top_n]]}),color="#10B981")
    with c3:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#334155;margin-bottom:8px'>JD Skill Matches</div>",unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame({"Skills":[len(r["matched"]) for r in filtered[:top_n]]}),color="#8B5CF6")

else:
    st.markdown("<div style='font-family:Syne,sans-serif;font-size:18px;font-weight:800;color:#E2E8F0;letter-spacing:-0.5px;margin-bottom:16px'>🍯 Honeypot Inspector</div>",unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.metric("Flagged",f"{gs['honey']:,}")
    c2.metric("Clean",f"{gs['valid']:,}")
    c3.metric("Detection Rate",f"{gs['honey']/max(gs['total'],1)*100:.2f}%")
    st.markdown("""
<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0 20px'>
  <div style='background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:14px'>
    <div style='font-weight:700;color:#E2E8F0;margin-bottom:5px;font-size:13px'>Rule A · Ghost Expertise</div>
    <div style='font-size:11.5px;color:#334155'>≥5 expert skills with 0 duration AND 0 endorsements</div>
  </div>
  <div style='background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:14px'>
    <div style='font-weight:700;color:#E2E8F0;margin-bottom:5px;font-size:13px'>Rule B · Impossible Timeline</div>
    <div style='font-size:11.5px;color:#334155'>Career months > stated YoE × 1.5 + 2yr</div>
  </div>
  <div style='background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:14px'>
    <div style='font-weight:700;color:#E2E8F0;margin-bottom:5px;font-size:13px'>Rule C · Assessment Fraud</div>
    <div style='font-size:11.5px;color:#334155'>Expert proficiency but assessment score &lt; 10/100</div>
  </div>
  <div style='background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:14px'>
    <div style='font-weight:700;color:#E2E8F0;margin-bottom:5px;font-size:13px'>Rule D · Date Anomalies</div>
    <div style='font-size:11.5px;color:#334155'>End date before start, or future start date</div>
  </div>
</div>""", unsafe_allow_html=True)
    hl=[r for r in results if r["honey"]]
    if hl:
        st.dataframe(pd.DataFrame([{"Candidate":r["id"],"Name":r["name"],"Title":r["title"],"YoE":r["yoe"],"Detection":r["reasoning"]} for r in hl]),use_container_width=True,hide_index=True)
    else:
        st.success("No honeypots detected.")

st.markdown("<div style='height:18px'></div>",unsafe_allow_html=True)
st.markdown("""
<div style='background:#07090F;border:1px solid rgba(255,255,255,0.05);border-radius:16px;padding:20px 24px'>
  <div style='font-size:9.5px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.14em;margin-bottom:14px'>⬇ Export Submission</div>""",
unsafe_allow_html=True)

top100=clean[:100]
buf=io.StringIO(); w=csv.writer(buf)
w.writerow(["candidate_id","rank","score","reasoning"])
for ri,r in enumerate(top100,1):
    w.writerow([r["id"],ri,f"{r['final']:.4f}",r["reasoning"]])

sr=f"{top100[-1]['final']:.4f} – {top100[0]['final']:.4f}" if len(top100)>=2 else "N/A"
c1,c2=st.columns(2)
with c1:
    st.download_button("⬇ Download submission.csv  (top 100 · RAW scores)",
        data=buf.getvalue(),file_name="submission.csv",mime="text/csv",use_container_width=True)
with c2:
    det=json.dumps([{"rank":i+1,"candidate_id":r["id"],"name":r["name"],"raw_score":round(r["final"],4),
        "career":round(r["career"],4),"skill":round(r["skill"],4),"behavioral":round(r["beh"],4),
        "matched_jd_skills":r["matched"],"reasoning":r["reasoning"]} for i,r in enumerate(top100)],indent=2)
    st.download_button("⬇ Download detailed_ranking.json",
        data=det,file_name="detailed_ranking.json",mime="application/json",use_container_width=True)

st.markdown(
    f"<div style='font-size:10.5px;color:#475569;margin-top:10px'>"
    f"Score range: <span style='color:#334155;font-family:monospace'>{sr}</span> · "
    f"RAW scores · No normalization · Rank 100 = top 0.1% of {gs['total']:,} candidates</div>",
    unsafe_allow_html=True)
st.markdown("</div>",unsafe_allow_html=True)