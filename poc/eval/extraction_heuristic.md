# Extraction eval (heuristic: keyword lexicon)

Synthetic rows from `data/orders.csv`, scored against the generator's latent labels, not human labels.

| Metric | Result |
|---|---|
| Rows evaluated | 300 (extraction failed on 0) |
| Address specificity, exact match (0-3) | 300/300 |
| Address specificity, within 1 level | 300/300 |
| Note intent recall (hesitation / reschedule / third-party flag found) | 96/133 |
| Notes with no risk intent that got a red flag (false positives) | 0/167 |

Caveat: the heuristic lexicon and the generator's address templates were written together, so address specificity is close to trivially recoverable here. Note intent includes paraphrases outside the lexicon on purpose, so its recall is the more honest number.
