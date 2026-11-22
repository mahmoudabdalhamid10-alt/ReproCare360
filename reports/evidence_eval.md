# Evidence AI retrieval evaluation

Dev queries were written while tuning; held-out queries were written afterwards and never tuned on.

| Configuration | Dev R@1 | Held-out R@1 | Held-out R@3 | Held-out MRR |
|---|---|---|---|---|
| TF-IDF only | 0.83 | 0.40 | 0.50 | 0.48 |
| BM25 only | 0.83 | 0.40 | 0.40 | 0.46 |
| Hybrid fusion | 0.83 | 0.40 | 0.50 | 0.47 |
| Hybrid + query expansion | 0.88 | 0.65 | 0.70 | 0.69 |

Held-out n=20, so uncertainty is wide (about +/-0.18 on R@1).

## Held-out misses (hybrid + expansion)

- we have been trying for a baby for over a year, what now
- i had the flu last month, when will my semen results reflect my new habits
- one testicle never descended, does it matter now
- am i too old to become a father at 48

## Unrelated-query rejection

4 of 5 unrelated queries were correctly rejected.
- REJECTED: how to change a car tire
- REJECTED: best recipe for chocolate cake
- ANSWERED: who won the football world cup
- REJECTED: python list comprehension tutorial
- REJECTED: cheap flights to istanbul
