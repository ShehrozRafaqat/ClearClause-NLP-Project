"""Risk scoring for ClearClause findings."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from .catalog import DIMENSIONS
from .models import ClauseFinding, RiskProfile


# Curve shape for the upper half of the risk scale. Below CURVE_PIVOT the
# score grows linearly with raw contributions. Above the pivot we apply an
# exponential compression so that increasingly bad contracts are
# distinguishable from each other without all saturating at 100.
CURVE_PIVOT = 60.0
CURVE_RANGE = 36.0   # asymptotic ceiling above the pivot (so cap is 96)
CURVE_SCALE = 160.0  # larger = slower compression


def _curve(raw: float) -> int:
    if raw <= CURVE_PIVOT:
        return int(round(max(0.0, raw)))
    excess = raw - CURVE_PIVOT
    compressed = CURVE_RANGE * (1.0 - math.exp(-excess / CURVE_SCALE))
    return int(round(min(100.0, CURVE_PIVOT + compressed)))


def calculate_risk(findings: list[ClauseFinding]) -> RiskProfile:
    counts = Counter(f.severity for f in findings)
    raw_score = 0.0
    dimension_raw: dict[str, float] = defaultdict(float)
    dimension_caps: dict[str, float] = defaultdict(float)

    for finding in findings:
        confidence_factor = 0.55 + (finding.confidence * 0.45)
        red_flag_bonus = min(6, len(finding.red_flags) * 2)
        green_discount = min(4, len(finding.green_flags) * 1.5)
        contribution = max(0, finding.adjusted_weight + red_flag_bonus - green_discount)
        contribution *= confidence_factor
        raw_score += contribution
        dimension_raw[finding.dimension] += contribution
        dimension_caps[finding.dimension] += 34

    high_pressure = counts["HIGH"] * 3.5
    medium_pressure = counts["MEDIUM"] * 1.25
    raw_total = raw_score + high_pressure + medium_pressure
    score = _curve(raw_total)

    if score >= 78:
        label = "Critical Risk"
        tone = "#c2410c"
    elif score >= 60:
        label = "High Risk"
        tone = "#dc2626"
    elif score >= 30:
        label = "Review Carefully"
        tone = "#b45309"
    else:
        label = "Low Risk"
        tone = "#15803d"

    dimension_scores = {}
    for key in DIMENSIONS:
        cap = max(35.0, dimension_caps.get(key, 35.0))
        dimension_scores[DIMENSIONS[key]] = min(100, round((dimension_raw.get(key, 0.0) / cap) * 100))

    top_flags = []
    for finding in sorted(findings, key=lambda f: (f.severity != "HIGH", -f.adjusted_weight, -f.confidence)):
        if finding.severity == "HIGH":
            top_flags.append(f"{finding.title}: {finding.business_impact}")
        if len(top_flags) == 4:
            break

    return RiskProfile(
        score=score,
        label=label,
        tone=tone,
        high_count=counts["HIGH"],
        medium_count=counts["MEDIUM"],
        low_count=counts["LOW"],
        info_count=counts["INFO"],
        dimension_scores=dimension_scores,
        top_flags=top_flags,
    )

