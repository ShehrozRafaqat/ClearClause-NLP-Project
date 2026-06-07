"""Negotiation coach: turns clause findings into actionable guidance.

This module is the bridge between the NLP layer (which only detects clauses)
and the product layer (which has to coach a non-lawyer through a contract).
It produces three artefacts:

1. A prioritised checklist of negotiation actions, ranked by business impact.
2. A fair-contract benchmark that compares each detected clause to a balanced
   industry-standard version of the same clause.
3. A short list of suggested discovery questions tailored to the risks
   actually found in this document.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import CATEGORY_ORDER, RULE_BY_ID
from .models import AnalysisResult, ClauseFinding


@dataclass(frozen=True)
class NegotiationItem:
    priority: int
    severity: str
    title: str
    category: str
    confidence: float
    actions: list[str]
    rationale: str


@dataclass(frozen=True)
class BenchmarkRow:
    title: str
    category: str
    status: str  # "fair", "concerning", "high-risk", "missing"
    severity: str
    fair_standard: str
    detected_text: str
    gap: str


# Clauses that a balanced freelance / professional contract should at least
# *address*, even if briefly. Missing any of these is itself an information
# gap worth flagging in the benchmark view.
EXPECTED_CORE_CLAUSES = [
    "scope_acceptance",
    "payment_terms",
    "ip_ownership",
    "confidentiality",
    "liability_cap",
    "unilateral_termination",
    "term_effective_date",
    "governing_law",
]


def build_checklist(findings: list[ClauseFinding]) -> list[NegotiationItem]:
    """Rank actionable negotiation items by severity, red-flag pressure, and confidence."""

    severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    items: list[NegotiationItem] = []
    for finding in findings:
        if not finding.negotiation_actions:
            continue
        if finding.severity == "INFO":
            # INFO clauses are recorded but they aren't negotiation priorities.
            continue
        rationale = finding.business_impact or finding.why_it_matters
        items.append(
            NegotiationItem(
                priority=0,
                severity=finding.severity,
                title=finding.title,
                category=finding.category or "Other",
                confidence=finding.confidence,
                actions=list(finding.negotiation_actions),
                rationale=rationale,
            )
        )

    items.sort(
        key=lambda item: (
            severity_rank.get(item.severity, 9),
            -item.confidence,
            item.title,
        )
    )
    return [
        NegotiationItem(
            priority=idx + 1,
            severity=item.severity,
            title=item.title,
            category=item.category,
            confidence=item.confidence,
            actions=item.actions,
            rationale=item.rationale,
        )
        for idx, item in enumerate(items)
    ]


def build_benchmark(findings: list[ClauseFinding]) -> list[BenchmarkRow]:
    """Compare each expected core clause + each detected clause to its fair standard."""

    findings_by_id = {finding.clause_id: finding for finding in findings}
    rows: list[BenchmarkRow] = []

    # 1) Score every detected clause against its fair standard.
    for finding in findings:
        rule = RULE_BY_ID.get(finding.clause_id)
        if rule is None or not rule.fair_standard:
            continue
        status, gap = _clause_status(finding)
        detected = finding.snippet.strip().replace("\n", " ")
        if len(detected) > 360:
            detected = detected[:360].rsplit(" ", 1)[0] + "..."
        rows.append(
            BenchmarkRow(
                title=finding.title,
                category=finding.category or "Other",
                status=status,
                severity=finding.severity,
                fair_standard=rule.fair_standard,
                detected_text=detected,
                gap=gap,
            )
        )

    # 2) Flag expected core clauses that were never detected.
    for clause_id in EXPECTED_CORE_CLAUSES:
        if clause_id in findings_by_id:
            continue
        rule = RULE_BY_ID.get(clause_id)
        if rule is None:
            continue
        rows.append(
            BenchmarkRow(
                title=rule.title,
                category=rule.category or "Other",
                status="missing",
                severity=rule.severity,
                fair_standard=rule.fair_standard,
                detected_text="Not found in this contract.",
                gap=(
                    "This clause is a standard part of a balanced contract but was not detected. "
                    "Ask the other party whether the topic is intentionally omitted or simply "
                    "handled informally."
                ),
            )
        )

    category_index = {name: idx for idx, name in enumerate(CATEGORY_ORDER)}
    status_rank = {"high-risk": 0, "concerning": 1, "missing": 2, "fair": 3}
    rows.sort(
        key=lambda row: (
            status_rank.get(row.status, 9),
            category_index.get(row.category, 99),
            row.title,
        )
    )
    return rows


def suggested_questions(result: AnalysisResult, limit: int = 6) -> list[str]:
    """Return discovery questions tied to the actual high/medium risks detected."""

    asked: set[str] = set()
    questions: list[str] = []
    for finding in result.findings:
        if finding.severity not in {"HIGH", "MEDIUM"}:
            continue
        for question in finding.questions:
            key = question.strip().lower()
            if key and key not in asked:
                asked.add(key)
                questions.append(question)
                break
        if len(questions) >= limit:
            break

    if len(questions) < limit:
        fallback = [
            "What are the top risks in this contract?",
            "Who owns the final work and source files?",
            "When will I be paid and what can the client withhold?",
            "Can the client terminate without cause? Will I be paid for work performed?",
            "Is my liability capped, and is the cap mutual?",
            "Are there any restrictions on future work?",
        ]
        for question in fallback:
            key = question.strip().lower()
            if key not in asked:
                asked.add(key)
                questions.append(question)
            if len(questions) >= limit:
                break

    return questions[:limit]


def _clause_status(finding: ClauseFinding) -> tuple[str, str]:
    severity = finding.severity
    red = len(finding.red_flags)
    green = len(finding.green_flags)

    if severity == "HIGH" and red >= 1:
        return (
            "high-risk",
            "Detected language is materially harsher than the fair standard. Treat this as a "
            "must-fix before signing.",
        )
    if severity == "HIGH":
        return (
            "concerning",
            "Topic carries high inherent risk. The detected language did not include obvious "
            "balancing terms — push it closer to the fair standard.",
        )
    if severity == "MEDIUM" and red > green:
        return (
            "concerning",
            "Detected language leans against you. Look for the small wording changes listed in "
            "the negotiation checklist.",
        )
    if severity == "MEDIUM":
        return (
            "fair",
            "Clause is broadly aligned with the fair standard. Verify wording during a final "
            "read-through.",
        )
    if severity == "LOW" and red > 0:
        return (
            "concerning",
            "Low-severity topic but with one or more red-flag phrases. Quick wording fixes are "
            "usually enough.",
        )
    return (
        "fair",
        "Clause largely matches the fair standard.",
    )
