"""Deterministic contract summary generation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import ClauseFinding, ParsedDocument, RiskProfile


@dataclass(frozen=True)
class Verdict:
    """Plain-English decision verdict derived from the risk profile."""

    label: str
    one_liner: str
    body: str
    css_class: str


def _first_match(patterns: list[str], text: str, default: str = "Not clearly stated") -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value = " ".join(group.strip() for group in match.groups() if group and group.strip())
            return re.sub(r"\s+", " ", value or match.group(0)).strip(" .")
    return default


def _amounts(text: str) -> list[str]:
    patterns = [
        r"\$\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:per|/)\s?(?:hour|month|project|milestone))?",
        r"\b(?:USD|PKR|Rs\.?)\s?\d[\d,]*(?:\.\d+)?",
        r"\bnet\s?(?:7|15|30|45|60|90)\b",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    deduped = []
    for item in found:
        normalized = item.strip()
        if normalized.lower() not in {x.lower() for x in deduped}:
            deduped.append(normalized)
    return deduped[:6]


def build_summary(document: ParsedDocument, findings: list[ClauseFinding], risk: RiskProfile) -> str:
    text = document.text
    parties = _first_match(
        [
            r"between\s+(.{2,100}?)\s+(?:and|&)\s+(.{2,100}?)(?:\.|\n|,)",
            r"by\s+and\s+between\s+(.{2,100}?)\s+(?:and|&)\s+(.{2,100}?)(?:\.|\n|,)",
        ],
        text,
    )
    effective = _first_match(
        [
            r"effective\s+(?:date\s+)?(?:as\s+of\s+)?([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            r"entered\s+into\s+(?:as\s+of\s+)?([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            r"commenc(?:es|ing)\s+on\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        ],
        text,
    )
    money = ", ".join(_amounts(text)) or "Not clearly stated"

    high = [f for f in findings if f.severity == "HIGH"]
    medium = [f for f in findings if f.severity == "MEDIUM"]
    top_risks = high[:4] or medium[:4]
    risk_lines = (
        "\n".join(f"- **{f.title}** — {f.recommendation}" for f in top_risks)
        or "- No major high-risk clauses were detected."
    )

    obligations = []
    for title in ("Scope, Acceptance & Revisions", "Confidentiality / NDA", "Payment Terms", "Effective Date & Term"):
        match = next((f for f in findings if f.title == title), None)
        if match:
            obligations.append(f"- {match.plain_english}")
    if not obligations:
        obligations.append(
            "- The document should be reviewed manually for obligations because few standard clauses were detected."
        )

    return (
        "### Executive Snapshot\n"
        f"- **Document:** {document.filename} ({document.word_count} words, "
        f"{document.page_count} estimated page(s)).\n"
        f"- **Parties / context:** {parties}.\n"
        f"- **Effective date:** {effective}.\n"
        f"- **Overall assessment:** {risk.label} with a score of {risk.score}/100.\n"
        f"- **Payment clues:** {money}.\n\n"
        "### Main Obligations Detected\n"
        + "\n".join(obligations[:5])
        + "\n\n### Priority Risks To Discuss Before Signing\n"
        + risk_lines
        + "\n\n### Suggested Decision\n"
        + _decision_line(risk)
    )


def build_verdict(risk: RiskProfile) -> Verdict:
    """Compact decision card used by the dashboard."""

    if risk.score >= 78:
        return Verdict(
            label="Critical Risk",
            css_class="CRITICAL",
            one_liner="Do not sign in the current form.",
            body=(
                "This contract concentrates several high-severity clauses against one party. "
                "Push for revisions on the priority red flags below before any signature. "
                "Most of the risky language is fixable with the suggested negotiation actions."
            ),
        )
    if risk.score >= 60:
        return Verdict(
            label="High Risk",
            css_class="HIGH",
            one_liner="Review carefully — revisions are recommended before signing.",
            body=(
                "Multiple clauses lean against the freelancer or smaller party. Work through the "
                "negotiation checklist and convert the one-sided clauses to mutual versions, "
                "then re-analyze the revised draft."
            ),
        )
    if risk.score >= 30:
        return Verdict(
            label="Review Carefully",
            css_class="REVIEW",
            one_liner="Manageable risk, but a few clauses should be clarified in writing.",
            body=(
                "The overall structure is acceptable, but specific clauses still benefit from "
                "small wording fixes. Use the negotiation checklist as a final read-through aid."
            ),
        )
    return Verdict(
        label="Low Risk",
        css_class="LOW",
        one_liner="The contract appears reasonably balanced based on the detected clauses.",
        body=(
            "No major red-flag concentrations were detected. Do a final manual review for "
            "anything outside the standard clause catalog and confirm dates and amounts match "
            "what was agreed verbally."
        ),
    )


def _decision_line(risk: RiskProfile) -> str:
    if risk.score >= 78:
        return (
            "**Do not sign in the current form.** Ask for revisions on the high-risk clauses first, "
            "especially money exposure, ownership, and future-work restrictions."
        )
    if risk.score >= 60:
        return (
            "**Review carefully before signing.** The contract may be acceptable only after specific "
            "risk clauses are narrowed or made mutual."
        )
    if risk.score >= 30:
        return "**Acceptable with edits.** Several clauses should still be clarified in writing."
    return (
        "**Largely acceptable.** The detected clauses are balanced, but a final manual review is "
        "still recommended."
    )
