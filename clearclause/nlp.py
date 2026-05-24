"""Hybrid NLP pipeline for clause extraction and contract analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .catalog import CLAUSE_RULES, SEVERITY_ORDER
from .document_io import parse_text
from .models import AnalysisResult, ClauseFinding, ClauseRule, ParsedDocument
from .scoring import calculate_risk
from .summarizer import build_summary


@dataclass(frozen=True)
class Section:
    index: int
    title: str
    text: str
    start: int
    end: int


def split_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    # Note: ``\Z`` is used instead of ``$`` because we are in multiline mode and
    # ``$`` would also match every end-of-line, fragmenting clauses into single
    # lines (e.g. a heading would be split from the paragraph that follows it).
    block_pattern = re.compile(r"(?ms)(?:^|\n)([^\n].*?)(?=\n\s*\n|\Z)")

    for index, match in enumerate(block_pattern.finditer(text)):
        block = match.group(1).strip()
        if not block:
            continue
        first_line = block.splitlines()[0].strip()
        title = _infer_title(first_line, block, index)
        sections.append(
            Section(
                index=len(sections),
                title=title,
                text=re.sub(r"\s+", " ", block).strip(),
                start=match.start(1),
                end=match.end(1),
            )
        )

    if not sections and text.strip():
        sections.append(Section(0, "Document", re.sub(r"\s+", " ", text).strip(), 0, len(text)))
    return sections


def analyze_contract(document: ParsedDocument | str, filename: str = "contract.txt") -> AnalysisResult:
    parsed = parse_text(document, filename=filename) if isinstance(document, str) else document
    sections = split_sections(parsed.text)
    findings = extract_clauses(parsed.text, sections)
    risk = calculate_risk(findings)
    summary = build_summary(parsed, findings, risk)

    avg_confidence = (
        round(sum(f.confidence for f in findings) / len(findings), 3) if findings else 0.0
    )
    avg_semantic = (
        round(sum(f.semantic_score for f in findings) / len(findings), 3) if findings else 0.0
    )
    diagnostics = {
        "sections_analyzed": len(sections),
        "rules_evaluated": len(CLAUSE_RULES),
        "findings_detected": len(findings),
        "high_confidence_findings": sum(1 for f in findings if f.confidence >= 0.75),
        "average_confidence": avg_confidence,
        "average_semantic_similarity": avg_semantic,
        "method": "regex pattern matching + TF-IDF semantic similarity",
    }
    return AnalysisResult(parsed, findings, risk, summary, diagnostics)


def extract_clauses(text: str, sections: list[Section] | None = None) -> list[ClauseFinding]:
    sections = sections or split_sections(text)
    if not sections:
        return []

    findings: list[ClauseFinding] = []
    section_texts = [section.text for section in sections]

    for rule in CLAUSE_RULES:
        semantic_scores = _semantic_scores(rule, section_texts)
        best: tuple[float, Section, list[str], list[str], list[str], float] | None = None

        for idx, section in enumerate(sections):
            matched_terms = _matched_terms(rule.patterns, section.text)
            red_flags = _matched_terms(rule.red_flags, section.text)
            green_flags = _matched_terms(rule.green_flags, section.text)
            semantic = float(semantic_scores[idx]) if idx < len(semantic_scores) else 0.0
            confidence = _confidence(rule, matched_terms, red_flags, green_flags, semantic, section)

            if confidence <= 0:
                continue
            if best is None or confidence > best[0]:
                best = (confidence, section, matched_terms, red_flags, green_flags, semantic)

        if best is None:
            continue

        confidence, section, matched_terms, red_flags, green_flags, semantic = best
        if confidence < _minimum_confidence(rule):
            continue

        severity = _adjusted_severity(rule.severity, red_flags, green_flags)
        adjusted_weight = _adjusted_weight(rule, severity, red_flags, green_flags, confidence)
        snippet, start, end = _best_snippet(section, matched_terms or red_flags)
        if not matched_terms and semantic >= 0.28:
            matched_terms = ["semantic match"]

        findings.append(
            ClauseFinding(
                clause_id=rule.clause_id,
                title=rule.title,
                severity=severity,
                base_weight=rule.base_weight,
                adjusted_weight=adjusted_weight,
                confidence=round(min(0.98, confidence), 3),
                snippet=snippet,
                section_title=section.title,
                start_char=section.start + start,
                end_char=section.start + end,
                matched_terms=_unique(matched_terms)[:8],
                red_flags=_unique(red_flags)[:6],
                green_flags=_unique(green_flags)[:6],
                why_it_matters=rule.why_it_matters,
                business_impact=rule.business_impact,
                recommendation=rule.recommendation,
                plain_english=_plain_english(rule, red_flags, green_flags),
                questions=rule.questions,
                dimension=rule.dimension,
                fair_standard=rule.fair_standard,
                negotiation_actions=list(rule.negotiation_actions),
                category=rule.category,
                semantic_score=round(semantic, 3),
            )
        )

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), -f.adjusted_weight, -f.confidence, f.title))
    return findings


def _infer_title(first_line: str, block: str, index: int) -> str:
    compact = re.sub(r"\s+", " ", first_line).strip()
    if re.match(r"^(?:section|article)?\s*\d{1,2}[\).\s-]+", compact, flags=re.IGNORECASE):
        return compact[:80]
    if len(compact) <= 70 and compact.upper() == compact and re.search(r"[A-Z]", compact):
        return compact.title()
    if len(block) < 180:
        return compact[:80] or f"Section {index + 1}"
    return f"Section {index + 1}"


def _semantic_scores(rule: ClauseRule, sections: list[str]) -> np.ndarray:
    prototype = " ".join([rule.title, *rule.prototypes, *rule.patterns])
    corpus = [prototype, *sections]
    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform(corpus)
        return cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    except ValueError:
        return np.zeros(len(sections))


def _matched_terms(patterns: Iterable[str], text: str) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            term = re.sub(r"\s+", " ", match.group(0)).strip()
            if term:
                found.append(term)
    return _unique(found)


def _confidence(
    rule: ClauseRule,
    matched_terms: list[str],
    red_flags: list[str],
    green_flags: list[str],
    semantic: float,
    section: Section,
) -> float:
    if matched_terms:
        pattern_strength = min(0.38, len(matched_terms) * 0.075)
        flag_strength = min(0.12, (len(red_flags) + len(green_flags)) * 0.035)
        title_bonus = 0.06 if _title_mentions_rule(section.title, rule) else 0.0
        return 0.48 + pattern_strength + flag_strength + min(0.18, semantic * 0.42) + title_bonus

    semantic_threshold = 0.31 if rule.severity in {"HIGH", "MEDIUM"} else 0.34
    if semantic >= semantic_threshold and len(section.text.split()) >= 18:
        title_bonus = 0.08 if _title_mentions_rule(section.title, rule) else 0.0
        return min(0.72, 0.30 + semantic + title_bonus)
    return 0.0


def _title_mentions_rule(title: str, rule: ClauseRule) -> bool:
    title_lower = title.lower()
    important_words = [word for word in re.findall(r"[a-z]+", rule.title.lower()) if len(word) > 4]
    return any(word in title_lower for word in important_words)


def _minimum_confidence(rule: ClauseRule) -> float:
    if rule.severity == "INFO":
        return 0.42
    if rule.severity == "LOW":
        return 0.44
    return 0.46


def _adjusted_severity(base: str, red_flags: list[str], green_flags: list[str]) -> str:
    if base == "INFO":
        return base
    red = len(red_flags)
    green = len(green_flags)

    severity = base
    if red >= 1 and severity == "LOW":
        severity = "MEDIUM"
    elif red >= 2 and severity == "MEDIUM":
        severity = "HIGH"

    # Strong balancing language pulls a HIGH clause all the way to LOW. This
    # handles the case where a contract talks about IP/indemnity/liability in
    # a clearly mutual, capped, carve-out-friendly way.
    if green >= 3 and red == 0 and severity == "HIGH":
        return "LOW"

    if green >= 2 and green > red and severity == "HIGH":
        severity = "MEDIUM"
    if green >= 2 and green > red and severity == "MEDIUM":
        severity = "LOW"
    if green >= 1 and red == 0 and severity == "HIGH":
        severity = "MEDIUM"
    return severity


def _adjusted_weight(
    rule: ClauseRule,
    severity: str,
    red_flags: list[str],
    green_flags: list[str],
    confidence: float,
) -> int:
    severity_floor = {"HIGH": 16, "MEDIUM": 9, "LOW": 4, "INFO": 1}[severity]
    weight = max(rule.base_weight, severity_floor)
    weight += min(8, len(red_flags) * 3)
    weight -= min(5, len(green_flags) * 2)
    if confidence < 0.62:
        weight = round(weight * 0.82)
    return max(severity_floor, int(weight))


def _best_snippet(section: Section, terms: list[str], window: int = 760) -> tuple[str, int, int]:
    section_text = section.text
    if not section_text:
        return "", 0, 0

    positions = []
    for term in terms:
        if term == "semantic match":
            continue
        match = re.search(re.escape(term), section_text, flags=re.IGNORECASE)
        if match:
            positions.append(match.start())

    center = positions[0] if positions else min(len(section_text) // 2, 120)
    start = max(0, center - window // 3)
    end = min(len(section_text), start + window)

    while start > 0 and section_text[start - 1] not in ".;:\n":
        start -= 1
    while end < len(section_text) and section_text[end - 1] not in ".;:\n":
        end += 1

    snippet = section_text[start:end].strip()
    if len(snippet) > window + 80:
        snippet = snippet[: window + 80].rsplit(" ", 1)[0] + "..."
    return snippet, start, min(len(section_text), end)


def _plain_english(rule: ClauseRule, red_flags: list[str], green_flags: list[str]) -> str:
    parts = [rule.plain_template]
    if red_flags:
        parts.append("Red flag language found: " + ", ".join(_unique(red_flags)[:3]) + ".")
    if green_flags:
        parts.append("Balancing language found: " + ", ".join(_unique(green_flags)[:3]) + ".")
    return " ".join(parts)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        normalized = re.sub(r"\s+", " ", str(value)).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            unique_values.append(normalized)
            seen.add(key)
    return unique_values

