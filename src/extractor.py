"""
Module 2 – Clause Extractor
Hybrid approach:
  1. Keyword/pattern matching (fast, always available) — primary method
  2. Optional CUAD DeBERTa-v3 QA model (USE_CUAD_MODEL=true in .env)

Returns a list of DetectedClause dicts.
"""
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from config import CLAUSE_DEFINITIONS


@dataclass
class DetectedClause:
    clause_type: str
    risk_level: str       # HIGH / MEDIUM / LOW
    risk_score: int       # numeric weight
    icon: str
    color: str
    bg: str
    snippet: str          # extracted text snippet (~300 chars)
    context: str          # broader paragraph context
    why_it_matters: str
    standard_note: str
    simplified: str = ""  # filled later by AIEngine
    confidence: float = 1.0


def _find_best_snippet(text: str, keyword: str, window: int = 350) -> tuple[str, str]:
    """
    Find the paragraph containing `keyword` and return (snippet, full_paragraph).
    """
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return "", ""

    start = max(0, match.start() - window // 2)
    end   = min(len(text), match.end() + window // 2)

    # Expand to sentence boundaries
    while start > 0 and text[start] not in ".!?\n":
        start -= 1
    while end < len(text) and text[end] not in ".!?\n":
        end += 1

    snippet = text[start:end].strip()
    snippet = re.sub(r"\s+", " ", snippet)

    # Full paragraph context
    para_start = text.rfind("\n\n", 0, match.start())
    para_end   = text.find("\n\n", match.end())
    para_start = para_start + 2 if para_start != -1 else 0
    para_end   = para_end if para_end != -1 else len(text)
    context = text[para_start:para_end].strip()
    context = re.sub(r"\s+", " ", context)

    return snippet[:500], context[:800]


class KeywordExtractor:
    """Fast keyword-based clause extractor — no ML model needed."""

    def extract(self, text: str) -> list[DetectedClause]:
        clauses: list[DetectedClause] = []
        seen_types: set[str] = set()
        text_lower = text.lower()

        for clause_type, defn in CLAUSE_DEFINITIONS.items():
            if clause_type in seen_types:
                continue

            best_snippet = ""
            best_context = ""
            best_kw = ""
            best_conf = 0.0

            for kw in defn["keywords"]:
                if kw.lower() in text_lower:
                    snippet, context = _find_best_snippet(text, kw)
                    if snippet and len(snippet) > len(best_snippet):
                        best_snippet = snippet
                        best_context = context
                        best_kw = kw
                        # More keyword matches = higher confidence
                        count = text_lower.count(kw.lower())
                        best_conf = min(0.95, 0.6 + count * 0.1)

            if best_snippet:
                clauses.append(DetectedClause(
                    clause_type=clause_type,
                    risk_level=defn["risk_level"],
                    risk_score=defn["risk_score"],
                    icon=defn["icon"],
                    color=defn["color"],
                    bg=defn["bg"],
                    snippet=best_snippet,
                    context=best_context,
                    why_it_matters=defn["why_it_matters"],
                    standard_note=defn["standard_note"],
                    confidence=best_conf,
                ))
                seen_types.add(clause_type)

        # Sort: HIGH first, then MEDIUM, then LOW
        order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        clauses.sort(key=lambda c: (order[c.risk_level], -c.risk_score))
        return clauses


class CUADExtractor:
    """
    Optional CUAD DeBERTa-v3 extractor.
    Downloads ~500 MB on first use. Set USE_CUAD_MODEL=true in .env.
    """

    def __init__(self):
        self._pipeline = None

    def _load(self):
        if self._pipeline is None:
            from transformers import pipeline
            print("Loading CUAD model (first time only, ~500 MB)…")
            self._pipeline = pipeline(
                "question-answering",
                model="tomasonjo/deberta-v3-base-cuad",
                tokenizer="tomasonjo/deberta-v3-base-cuad",
                device=-1,  # CPU
            )
            print("CUAD model loaded ✓")

    def extract(self, text: str) -> list[DetectedClause]:
        self._load()
        clauses: list[DetectedClause] = []
        # Truncate for model (max 512 tokens per chunk)
        MAX_CONTEXT = 2000
        chunks = [text[i:i+MAX_CONTEXT] for i in range(0, min(len(text), 8000), MAX_CONTEXT)]

        for clause_type, defn in CLAUSE_DEFINITIONS.items():
            question = defn.get("simplify_hint", f"Is there a clause about {clause_type}?")
            question = f"Highlight the parts related to {clause_type}: {question}"

            best_answer = ""
            best_score  = 0.0
            for chunk in chunks:
                try:
                    result = self._pipeline(question=question, context=chunk)
                    if result["score"] > 0.1 and result["score"] > best_score:
                        best_answer = result["answer"]
                        best_score  = result["score"]
                except Exception:
                    continue

            if best_answer and best_score > 0.1:
                _, context = _find_best_snippet(text, best_answer[:30])
                clauses.append(DetectedClause(
                    clause_type=clause_type,
                    risk_level=defn["risk_level"],
                    risk_score=defn["risk_score"],
                    icon=defn["icon"],
                    color=defn["color"],
                    bg=defn["bg"],
                    snippet=best_answer[:500],
                    context=context,
                    why_it_matters=defn["why_it_matters"],
                    standard_note=defn["standard_note"],
                    confidence=round(best_score, 2),
                ))

        order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        clauses.sort(key=lambda c: (order[c.risk_level], -c.risk_score))
        return clauses


def get_extractor() -> KeywordExtractor | CUADExtractor:
    """Return the appropriate extractor based on env config."""
    use_cuad = os.getenv("USE_CUAD_MODEL", "false").lower() == "true"
    if use_cuad:
        return CUADExtractor()
    return KeywordExtractor()
