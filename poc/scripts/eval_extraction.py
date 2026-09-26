"""Extraction eval against the generator's latent labels (address quality, note intent).

    python scripts/eval_extraction.py            # heuristic, all rows
    python scripts/eval_extraction.py --llm --n 20

Writes eval/extraction_<source>.md. These are generator labels, not human labels: they say whether the
extractor recovers what the generator encoded, on synthetic text. Hand-label real rows before any claim.
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import config, db  # noqa: E402
from pipeline.extract import extract  # noqa: E402
from pipeline.llm import get_client  # noqa: E402

INTENT_TO_FLAG = {"hesitant": "hesitation", "reschedule": "reschedule", "third_party": "third_party_receiver"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--n", type=int, default=0, help="rows to evaluate (0 = all)")
    ap.add_argument("--rpm", type=int, default=25)
    a = ap.parse_args()
    client = get_client() if a.llm else None
    if a.llm and client is None:
        sys.exit("--llm needs LLM_PROVIDER and an API key")

    rows = pd.read_csv(config.DATA_CSV, keep_default_na=False)
    if a.n:
        rows = rows.sample(n=a.n, random_state=3)
    conn = db.connect(config.ROOT / "seed.db") if client else None

    spec_exact = spec_near = recall_hit = recall_n = fp = clean_n = failed = 0
    for _, r in rows.iterrows():
        ext = extract(r.address_text, r.note_text, client, conn)
        if client and not ext.cache_hit:
            time.sleep(60 / a.rpm)
        if ext.failed:
            failed += 1
            continue
        f = ext.flags
        spec_exact += f.address_specificity == r.latent_address_quality
        spec_near += abs(f.address_specificity - r.latent_address_quality) <= 1
        note_types = {x.type for x in f.red_flags if x.text in r.note_text}
        if r.latent_intent in INTENT_TO_FLAG:
            recall_n += 1
            recall_hit += INTENT_TO_FLAG[r.latent_intent] in note_types
        else:
            clean_n += 1
            fp += bool(note_types - {"other"})

    n = len(rows) - failed
    source = "llm" if client else "heuristic"
    model_name = client.model if client else "keyword lexicon"
    md = f"""# Extraction eval ({source}: {model_name})

Synthetic rows from `data/orders.csv`, scored against the generator's latent labels, not human labels.

| Metric | Result |
|---|---|
| Rows evaluated | {n} (extraction failed on {failed}) |
| Address specificity, exact match (0-3) | {spec_exact}/{n} |
| Address specificity, within 1 level | {spec_near}/{n} |
| Note intent recall (hesitation / reschedule / third-party flag found) | {recall_hit}/{recall_n} |
| Notes with no risk intent that got a red flag (false positives) | {fp}/{clean_n} |
"""
    if source == "heuristic":
        md += ("\nCaveat: the heuristic lexicon and the generator's address templates were written together, "
               "so address specificity is close to trivially recoverable here. Note intent includes "
               "paraphrases outside the lexicon on purpose, so its recall is the more honest number.\n")
    out = config.ROOT / "eval" / f"extraction_{source}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(md)
    print(md)


if __name__ == "__main__":
    main()
