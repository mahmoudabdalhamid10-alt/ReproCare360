"""Evidence AI: retrieval over a small curated knowledge base.

No generated text: a query returns source passages, ranked. The ranker is a
hybrid of TF-IDF and BM25 with a light stemmer and a lay-to-medical synonym
expansion ("weed" -> "cannabis"). Queries whose best score stays below a
confidence threshold are rejected instead of answered.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Lay / colloquial -> medical synonym groups. Both directions are indexed.
SYNONYMS: Dict[str, List[str]] = {
    "weed": ["cannabis", "marijuana"],
    "pot": ["cannabis", "marijuana"],
    "marijuana": ["cannabis"],
    "balls": ["testicle", "testicles", "testicular", "scrotum"],
    "ball": ["testicle", "testicles", "testicular"],
    "nuts": ["testicle", "testicles"],
    "sperm count": ["concentration", "oligospermia"],
    "low count": ["oligospermia", "concentration"],
    "shooting blanks": ["azoospermia"],
    "no sperm": ["azoospermia"],
    "sterile": ["infertility"],
    "cant conceive": ["infertility"],
    "can't conceive": ["infertility"],
    "hard to conceive": ["infertility", "subfertility"],
    "smokes": ["smoking", "tobacco"],
    "cigarettes": ["smoking", "tobacco"],
    "booze": ["alcohol"],
    "drinking": ["alcohol"],
    "hot tub": ["heat", "temperature"],
    "sauna": ["heat", "temperature"],
    "laptop": ["heat", "temperature"],
    "tight underwear": ["heat", "temperature"],
    "boxers": ["underwear", "heat"],
    "briefs": ["underwear", "heat"],
    "bike": ["cycling"],
    "bicycle": ["cycling"],
    "working out": ["exercise"],
    "fat": ["obesity", "weight", "bmi"],
    "overweight": ["obesity", "weight", "bmi"],
    "diet": ["nutrition", "food"],
    "vitamins": ["supplements", "antioxidants"],
    "pills": ["supplements", "medication"],
    "steroids": ["anabolic", "testosterone"],
    "testosterone booster": ["anabolic", "testosterone"],
    "chemo": ["chemotherapy"],
    "cancer treatment": ["chemotherapy", "radiotherapy"],
    "mumps": ["orchitis"],
    "stress": ["cortisol"],
    "sleep": ["circadian"],
    "age": ["paternal age"],
    "older dad": ["paternal age"],
    "prepare": ["collect", "abstinence"],
    "preparation": ["collect", "abstinence"],
    "repeat": ["retesting"],
    "gym": ["exercise"],
    "varicocele": ["veins", "scrotum"],
    "undescended": ["cryptorchidism"],
    "std": ["sti", "infection"],
    "clap": ["gonorrhea", "sti"],
    "chlamydia": ["sti", "infection"],
    "lubricant": ["lube"],
    "lube": ["lubricant"],
    "hot baths": ["heat", "temperature"],
    "phone pocket": ["radiation", "heat"],
    "tight jeans": ["heat", "temperature"],
}

_STOP = set("a an and are as at be by can could do does for from how i if in is it my of on or the to what when which why will with would your me "
            "change best make take long new matter bad good much many should".split())


def stem(token: str) -> str:
    """Very light English stemmer: strips common suffixes."""
    for suf in ("ies", "ing", "ed", "es", "s"):
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            if suf == "ies":
                return token[: -len(suf)] + "y"
            return token[: -len(suf)]
    return token


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9']+", text.lower())
    return [stem(t) for t in tokens if t not in _STOP and len(t) > 1]


def expand_query(tokens: List[str], text: str) -> List[str]:
    """Add medical synonyms for lay terms found in the query."""
    lowered = text.lower()
    extra: List[str] = []
    for lay, meds in SYNONYMS.items():
        if lay in lowered:
            extra.extend(stem(m) for m in meds)
    return tokens + extra


class KnowledgeBase:
    def __init__(self, path: Optional[Path] = None):
        path = path or (DATA_DIR / "knowledge_base.json")
        with open(path, encoding="utf-8") as fh:
            self.entries: List[Dict[str, str]] = json.load(fh)
        self._docs = [tokenize(e["title"] + " " + e["text"]) for e in self.entries]
        self._idf = self._build_idf()

    def _build_idf(self) -> Dict[str, float]:
        n = len(self._docs)
        df: Counter = Counter()
        for doc in self._docs:
            for tok in set(doc):
                df[tok] += 1
        return {tok: math.log(1 + (n - c + 0.5) / (c + 0.5)) for tok, c in df.items()}

    def get(self, entry_id: str) -> Optional[Dict[str, str]]:
        for e in self.entries:
            if e["id"] == entry_id:
                return e
        return None

    # -- scoring ---------------------------------------------------------
    def _tfidf_scores(self, query_tokens: List[str]) -> List[float]:
        scores = []
        q_counts = Counter(query_tokens)
        for doc in self._docs:
            d_counts = Counter(doc)
            score = 0.0
            for tok, qtf in q_counts.items():
                if tok in d_counts:
                    score += qtf * d_counts[tok] * self._idf.get(tok, 0.0)
            norm = math.sqrt(sum(c * c for c in d_counts.values())) or 1.0
            scores.append(score / norm)
        return scores

    def _bm25_scores(self, query_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
        avgdl = sum(len(d) for d in self._docs) / max(1, len(self._docs))
        scores = []
        for doc in self._docs:
            d_counts = Counter(doc)
            dl = len(doc)
            score = 0.0
            for tok in set(query_tokens):
                if tok not in d_counts:
                    continue
                tf = d_counts[tok]
                idf = self._idf.get(tok, 0.0)
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / (avgdl or 1)))
            scores.append(score)
        return scores

    @staticmethod
    def _normalize(scores: List[float]) -> List[float]:
        top = max(scores) if scores else 0.0
        if top <= 0:
            return [0.0] * len(scores)
        return [s / top for s in scores]

    def search(
        self,
        query: str,
        k: int = 3,
        method: str = "hybrid",
        expand: bool = True,
        min_score: float = 0.12,
    ) -> Dict[str, object]:
        base_tokens = tokenize(query)
        tokens = expand_query(base_tokens, query) if expand else base_tokens
        if not tokens:
            return {"query": query, "results": [], "rejected": True,
                    "reason": "empty query"}

        tfidf = self._normalize(self._tfidf_scores(tokens))
        bm25 = self._normalize(self._bm25_scores(tokens))
        if method == "tfidf":
            scores = tfidf
        elif method == "bm25":
            scores = bm25
        else:
            scores = [0.5 * (a + b) for a, b in zip(tfidf, bm25)]

        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        best = scores[ranked[0]] if ranked else 0.0
        # Rejection guard: normalized scores always peak at 1.0, so reject on
        # term coverage instead. A query passes when any top-5 passage shares
        # at least two expanded terms with it, or one term that covers a decent
        # share of the query's content words. Truly unrelated queries match
        # nothing under this rule.
        base_set = set(base_tokens)
        token_set = set(tokens)
        accepted = False
        for i in ranked[:5]:
            if scores[i] <= 0:
                continue
            doc_set = set(self._docs[i])
            matched = len(token_set & doc_set)
            coverage = len(base_set & doc_set) / max(1, len(base_set))
            if matched >= 2 or (matched >= 1 and coverage >= 0.25):
                accepted = True
                break
        if best <= 0 or not accepted:
            return {"query": query, "results": [], "rejected": True,
                    "reason": "no passage shares enough terms with the query"}
        results = []
        for i in ranked[:k]:
            if scores[i] <= 0:
                continue
            entry = dict(self.entries[i])
            entry["score"] = round(scores[i], 4)
            results.append(entry)
        return {"query": query, "results": results, "rejected": False, "method": method, "expanded": expand}
