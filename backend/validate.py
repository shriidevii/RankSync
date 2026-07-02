import argparse
import csv
import json
import re
import sys
 
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
W = "\033[0m"
B = "\033[1m"
 
 
def run(submission_path: str, candidates_path: str = None) -> bool:
    print(f"\n{B}Validating: {submission_path}{W}")
    print("─" * 52)
    all_pass = True
 
    def ok(msg):
        print(f"  {G}✓{W} {msg}")
 
    def fail(msg):
        nonlocal all_pass
        all_pass = False
        print(f"  {R}✗  {msg}{W}")
 
    def warn(msg):
        print(f"  {Y}!  {msg}{W}")
 
    try:
        content = open(submission_path, encoding="utf-8").read()
        ok("UTF-8 encoding")
    except Exception as e:
        fail(f"Cannot read file: {e}")
        return False
 
    try:
        rows = list(csv.DictReader(submission_path and open(submission_path, encoding="utf-8")))
        ok(f"CSV parses cleanly ({len(rows)} rows)")
    except Exception as e:
        fail(f"CSV parse error: {e}")
        return False
 
    required = {"candidate_id", "rank", "score", "reasoning"}
    if rows:
        missing_cols = required - set(rows[0].keys())
        if missing_cols:
            fail(f"Missing columns: {missing_cols}")
        else:
            ok(f"Required columns present")
 
    if len(rows) == 100:
        ok("Exactly 100 rows")
    else:
        fail(f"Expected 100 rows, got {len(rows)}")
 
    if not rows:
        fail("No data rows")
        return False
 
    try:
        ranks = [int(r["rank"]) for r in rows]
        if sorted(ranks) == list(range(1, 101)):
            ok("Ranks 1–100 each appear exactly once")
        else:
            fail(f"Ranks invalid: min={min(ranks)}, max={max(ranks)}")
    except ValueError as e:
        fail(f"Non-integer rank: {e}")
 
    ids = [r["candidate_id"] for r in rows]
    if len(set(ids)) == 100:
        ok("All candidate_ids unique")
    else:
        fail("Duplicate candidate_ids found")
 
    bad_fmt = [cid for cid in ids if not re.match(r"^CAND_\d{7}$", cid)]
    if bad_fmt:
        fail(f"Malformed IDs: {bad_fmt[:3]}")
    else:
        ok("All IDs match CAND_XXXXXXX format")
 
    try:
        scores = [float(r["score"]) for r in rows]
        ok("Scores are numeric")
        if all(0.0 <= s <= 1.0 for s in scores):
            ok("Scores in [0, 1]")
        else:
            fail("Scores outside [0, 1]")
        if all(scores[i] >= scores[i + 1] for i in range(99)):
            ok("Scores non-increasing with rank")
        else:
            fail("Scores not non-increasing")
        if len(set(scores)) > 1:
            ok(f"Score range: {min(scores):.4f} — {max(scores):.4f}")
        else:
            fail("All scores identical — model not differentiating")
    except ValueError as e:
        fail(f"Non-numeric score: {e}")
 
    reasons = [r.get("reasoning", "") for r in rows]
    empty = sum(1 for r in reasons if not r.strip())
    if empty == 0:
        ok("No empty reasoning strings")
    else:
        fail(f"{empty} empty reasoning strings")
    if len(set(reasons)) == 100:
        ok("All reasoning strings unique")
    else:
        warn(f"{100 - len(set(reasons))} duplicate reasoning strings")
 
    avg_len = sum(len(r) for r in reasons) / max(len(reasons), 1)
    if avg_len >= 30:
        ok(f"Avg reasoning length: {avg_len:.0f} chars")
    else:
        fail(f"Reasoning too short: avg {avg_len:.0f} chars")
 
    if candidates_path:
        valid_ids = set()
        with open(candidates_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    valid_ids.add(json.loads(line)["candidate_id"])
        unknown = [cid for cid in ids if cid not in valid_ids]
        if unknown:
            fail(f"IDs not in dataset: {unknown[:3]}")
        else:
            ok(f"All {len(ids)} IDs found in dataset")
 
    print("\n" + "─" * 52)
    if all_pass:
        print(f"  {G}{B}VALID — safe to submit{W}")
    else:
        print(f"  {R}{B}INVALID — fix errors before submitting{W}")
    return all_pass
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", required=True)
    parser.add_argument("--candidates", default=None)
    args = parser.parse_args()
    result = run(args.submission, args.candidates)
    sys.exit(0 if result else 1)
 

