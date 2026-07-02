import argparse
import sys
import time
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).parent))
 
 
def main():
    parser = argparse.ArgumentParser(description="Pre-compute candidate embeddings")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
 
    if not Path(args.candidates).exists():
        print(f"File not found: {args.candidates}")
        sys.exit(1)
 
    print("TalentLens — Embedding Pre-computation")
    print(f"Input:  {args.candidates}")
    print(f"Model:  all-MiniLM-L6-v2  (downloads ~80MB first run)")
    print()
 
    t0 = time.time()
    from embed import precompute
 
    embs, ids = precompute(args.candidates, batch_size=args.batch_size)
 
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"Candidates embedded: {len(ids):,}")
    print(f"Shape: {embs.shape}")
    print("\nNow run:")
    print(f"  python rank.py --candidates {args.candidates} --out submission.csv")
 
 
if __name__ == "__main__":
    main()
 

