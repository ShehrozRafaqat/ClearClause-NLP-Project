"""Inline redline rendering: highlight risky spans inside the contract text.

The Streamlit "Redline" view renders the full cleaned contract with HIGH /
MEDIUM / LOW spans visually highlighted, so the demo viewer can see exactly
where each finding lives in the document, not just an isolated snippet.

The pipeline records ``start_char`` and ``end_char`` for each finding, but
those positions are relative to a whitespace-normalised section, not the
cleaned full document. Rather than recomputing offsets through every layer,
we re-locate each finding's snippet inside the document text at render time
with a forgiving substring search. This keeps the data layer simple and the
renderer robust to small wording drifts.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from .models import ClauseFinding


SEVERITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    severity: str
    title: str
    clause_id: str


def _locate(snippet: str, text: str) -> tuple[int, int] | None:
    """Best-effort locate `snippet` (or a leading prefix) inside `text`."""

    if not snippet:
        return None
    needle = re.sub(r"\s+", " ", snippet).strip()
    if not needle:
        return None
    # Normalise text the same way we normalise the snippet so positions line up.
    haystack = re.sub(r"\s+", " ", text)

    # Try progressively shorter prefixes so small whitespace / punctuation
    # mismatches don't drop spans on the floor.
    for length in (len(needle), 220, 160, 100, 60):
        prefix = needle[:length].strip()
        if not prefix:
            continue
        idx = haystack.find(prefix)
        if idx >= 0:
            return idx, idx + len(prefix)
    return None


def _collect_spans(
    text: str,
    findings: list[ClauseFinding],
    severities: tuple[str, ...] = ("HIGH", "MEDIUM", "LOW"),
) -> tuple[str, list[_Span]]:
    """Locate every finding's snippet inside the normalised text."""

    normalised = re.sub(r"\s+", " ", text)
    spans: list[_Span] = []
    for finding in findings:
        if finding.severity not in severities:
            continue
        position = _locate(finding.snippet, text)
        if position is None:
            continue
        start, end = position
        spans.append(
            _Span(
                start=start,
                end=end,
                severity=finding.severity,
                title=finding.title,
                clause_id=finding.clause_id,
            )
        )
    return normalised, spans


def redline_html(
    text: str,
    findings: list[ClauseFinding],
    severities: tuple[str, ...] = ("HIGH", "MEDIUM", "LOW"),
) -> str:
    """Render the contract text as HTML with severity-coloured highlight spans."""

    normalised, spans = _collect_spans(text, findings, severities)
    if not normalised.strip():
        return "<div class='cc-redline'><em>No document text to render.</em></div>"

    n = len(normalised)
    # Per-character "winning" severity: HIGH overrides MEDIUM overrides LOW.
    owners: list[_Span | None] = [None] * n
    for span in spans:
        for i in range(span.start, min(span.end, n)):
            current = owners[i]
            if current is None or SEVERITY_RANK.get(span.severity, -1) > SEVERITY_RANK.get(
                current.severity, -1
            ):
                owners[i] = span

    parts: list[str] = []
    i = 0
    while i < n:
        owner = owners[i]
        j = i + 1
        while j < n and owners[j] is owner:
            j += 1
        chunk = html.escape(normalised[i:j])
        if owner is None:
            parts.append(chunk)
        else:
            tooltip = html.escape(owner.title)
            parts.append(
                f'<mark class="rl rl-{owner.severity}" title="{tooltip}" '
                f'data-clause="{owner.clause_id}">{chunk}</mark>'
            )
        i = j

    counts = {sev: 0 for sev in severities}
    for span in spans:
        counts[span.severity] = counts.get(span.severity, 0) + 1
    legend_items = []
    for sev in severities:
        if counts.get(sev):
            legend_items.append(
                f"<span class='rl-legend rl-legend-{sev}'>{sev} · {counts[sev]} span"
                f"{'s' if counts[sev] != 1 else ''}</span>"
            )
    legend = (
        f"<div class='rl-legend-row'>{''.join(legend_items)}</div>" if legend_items else ""
    )

    body = "".join(parts)
    return (
        "<div class='cc-redline-wrap'>"
        f"{legend}"
        f"<div class='cc-redline'>{body}</div>"
        "</div>"
    )
