"""Shared data models for the ClearClause pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    file_type: str
    text: str
    paragraphs: list[str]
    word_count: int
    char_count: int
    page_count: int
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ClauseRule:
    clause_id: str
    title: str
    severity: str
    base_weight: int
    patterns: list[str]
    prototypes: list[str]
    why_it_matters: str
    business_impact: str
    recommendation: str
    plain_template: str
    questions: list[str]
    dimension: str
    red_flags: list[str] = field(default_factory=list)
    green_flags: list[str] = field(default_factory=list)
    fair_standard: str = ""
    negotiation_actions: list[str] = field(default_factory=list)
    category: str = ""


@dataclass
class ClauseFinding:
    clause_id: str
    title: str
    severity: str
    base_weight: int
    adjusted_weight: int
    confidence: float
    snippet: str
    section_title: str
    start_char: int
    end_char: int
    matched_terms: list[str]
    red_flags: list[str]
    green_flags: list[str]
    why_it_matters: str
    business_impact: str
    recommendation: str
    plain_english: str
    questions: list[str]
    dimension: str
    fair_standard: str = ""
    negotiation_actions: list[str] = field(default_factory=list)
    category: str = ""
    semantic_score: float = 0.0


@dataclass(frozen=True)
class RiskProfile:
    score: int
    label: str
    tone: str
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    dimension_scores: dict[str, int]
    top_flags: list[str]


@dataclass
class AnalysisResult:
    document: ParsedDocument
    findings: list[ClauseFinding]
    risk: RiskProfile
    summary_markdown: str
    diagnostics: dict[str, str | int | float]
