from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z]+\d+|[A-Za-z_][A-Za-z0-9_]+|\d+(?:\.\d+)?")
CELL_QUERY_RE = re.compile(r"(?:'[^']+'|[A-Za-z0-9_ ]+!)?\$?[A-Z]{1,3}\$?\d+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "")]


@dataclass
class SearchResult:
    score: float
    doc: dict[str, Any]


class BM25Retriever:
    """Tiny BM25 retriever, dependency-free and good enough for local prototypes."""

    def __init__(self, docs: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.docs = docs
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(self._doc_text(d)) for d in docs]
        self.doc_len = [len(toks) for toks in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / max(len(self.doc_len), 1)
        self.df = defaultdict(int)
        for toks in self.doc_tokens:
            for term in set(toks):
                self.df[term] += 1
        self.N = len(docs)

    @staticmethod
    def _doc_text(doc: dict[str, Any]) -> str:
        return "\n".join([
            str(doc.get("text", "")),
            str(doc.get("label", "")),
            str(doc.get("address", "")),
            str(doc.get("formula", "")),
            str(doc.get("variable_name", "")),
            str(doc.get("js_formula_named", "")),
            str(doc.get("named_dependencies", "")),
            str(doc.get("section_title", "")),
            " ".join(doc.get("section_path", [])),
            " ".join(doc.get("section_references", [])),
            " ".join(doc.get("dependencies", [])),
        ])

    def search(self, query: str, top_k: int = 8) -> list[SearchResult]:
        exact_cell = [c.replace("$", "").upper() for c in CELL_QUERY_RE.findall(query)]
        q_terms = tokenize(query)
        if not q_terms and not exact_cell:
            return []

        scores = [0.0 for _ in self.docs]
        for i, doc in enumerate(self.docs):
            addr = str(doc.get("address", "")).upper()
            if addr in exact_cell:
                scores[i] += 100.0
            for dep in doc.get("dependencies", []):
                if dep.replace("$", "").upper() in exact_cell:
                    scores[i] += 35.0

        for term in q_terms:
            df = self.df.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
            for i, toks in enumerate(self.doc_tokens):
                tf = Counter(toks).get(term, 0)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * self.doc_len[i] / max(self.avgdl, 1))
                scores[i] += idf * (tf * (self.k1 + 1)) / denom

        ranked = sorted(
            [SearchResult(score=s, doc=d) for s, d in zip(scores, self.docs) if s > 0],
            key=lambda x: x.score,
            reverse=True,
        )
        return ranked[:top_k]


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def format_context(results: list[SearchResult], max_chars: int = 12000) -> str:
    parts: list[str] = []
    total = 0
    for idx, result in enumerate(results, start=1):
        d = result.doc
        block = f"""
[RESULT {idx}] score={result.score:.4f}
Source: {d.get('sheet')}!{d.get('address')}
Section: {' > '.join(d.get('section_path', []))}
Section rows: {d.get('section_range')}
Section references: {' | '.join(d.get('section_references', []))}
Label: {d.get('label')}
Value: {d.get('value')}
Formula: {d.get('formula')}
Variable name: {d.get('variable_name')}
Variable role: {d.get('variable_role')}
Named dependencies: {d.get('named_dependencies')}
Named JS formula: {d.get('js_formula_named')}
Dependencies: {', '.join(d.get('dependencies', []))}
Risk: {d.get('risk_level')} {', '.join(d.get('risk_reasons', []))}
JS hint: {d.get('js_hint')}
Section calculation chain: {d.get('section_calculations')}
Nearby context: {d.get('nearby_context')}
""".strip()
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)
