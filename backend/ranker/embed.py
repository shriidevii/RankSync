import json
import numpy as np
from pathlib import Path
 
MODEL_NAME = "all-MiniLM-L6-v2"
CACHE_DIR = Path(__file__).parent.parent / "cache"
EMBED_FILE = CACHE_DIR / "candidate_embeddings.npy"
ID_FILE = CACHE_DIR / "candidate_ids.json"
JD_EMBED_FILE = CACHE_DIR / "jd_embedding.npy"
 
JD_TEXT = (
    "Senior AI Engineer production embeddings retrieval ranking systems "
    "vector database hybrid search sentence-transformers Pinecone Weaviate "
    "Qdrant FAISS Elasticsearch OpenSearch BM25 NDCG MRR MAP evaluation "
    "framework Python PyTorch fine-tuning LLMs LoRA PEFT RAG recommendation "
    "systems learning to rank 5-9 years production experience product company "
    "startup applied machine learning NLP information retrieval"
)
 
 
def load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)
 
 
def precompute(candidates_path: str, batch_size: int = 512):
    from features import get_text_for_embedding
 
    CACHE_DIR.mkdir(exist_ok=True)
    model = load_model()
 
    jd_emb = model.encode([JD_TEXT], normalize_embeddings=True)[0]
    np.save(JD_EMBED_FILE, jd_emb)
 
    texts, ids = [], []
    with open(candidates_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            ids.append(c["candidate_id"])
            texts.append(get_text_for_embedding(c))
            if (i + 1) % 10000 == 0:
                print(f"  Read {i+1:,} candidates...")
 
    print(f"Embedding {len(texts):,} candidates...")
    embs = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
 
    np.save(EMBED_FILE, embs)
    with open(ID_FILE, "w") as f:
        json.dump(ids, f)
 
    print(f"Saved embeddings: shape={embs.shape}")
    return embs, ids
 
 
def load():
    if not EMBED_FILE.exists() or not ID_FILE.exists():
        raise FileNotFoundError(
            "Embeddings not found. Run:\n  python precompute.py --candidates <path>"
        )
    embs = np.load(EMBED_FILE)
    with open(ID_FILE) as f:
        ids = json.load(f)
    return embs, ids
 
 
def semantic_scores(jd_emb: np.ndarray, candidate_embs: np.ndarray) -> np.ndarray:
    scores = candidate_embs @ jd_emb
    return ((scores + 1.0) / 2.0).astype(np.float32)
 
 
def load_jd_embedding() -> np.ndarray:
    if not JD_EMBED_FILE.exists():
        CACHE_DIR.mkdir(exist_ok=True)
        model = load_model()
        emb = model.encode([JD_TEXT], normalize_embeddings=True)[0]
        np.save(JD_EMBED_FILE, emb)
        return emb
    return np.load(JD_EMBED_FILE)
 

