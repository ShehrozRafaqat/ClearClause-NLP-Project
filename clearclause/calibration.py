"""Confidence calibration analysis for ClearClause.

For an explainable NLP system the *confidence* score on each finding has to
actually correlate with whether the finding is correct, otherwise the number
is just visual decoration. This module computes that correlation across one
or more labelled contracts and returns:

- per-finding (confidence, correct) data points;
- equal-width confidence bins with the empirical precision inside each bin;
- a Brier score and the expected calibration error (ECE) for the run.

The Streamlit "Pipeline & Evaluation" tab uses this to render a reliability
diagram alongside the gold precision / recall / F1 numbers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import AnalysisResult, ClauseFinding
from .nlp import analyze_contract


@dataclass(frozen=True)
class CalibrationPoint:
    confidence: float
    correct: int   # 1 if clause_id is in the expected set, 0 otherwise
    clause_id: str
    severity: str
    demo: str


@dataclass(frozen=True)
class CalibrationBin:
    low: float
    high: float
    count: int
    correct: int
    mean_confidence: float
    precision: float


@dataclass(frozen=True)
class CalibrationReport:
    points: list[CalibrationPoint]
    bins: list[CalibrationBin]
    overall_precision: float
    brier: float
    ece: float


DEFAULT_BIN_EDGES: tuple[float, ...] = (0.0, 0.55, 0.70, 0.85, 1.01)


def _evaluate_one(analysis: AnalysisResult, expected: set[str], demo_name: str) -> list[CalibrationPoint]:
    return [
        CalibrationPoint(
            confidence=float(finding.confidence),
            correct=1 if finding.clause_id in expected else 0,
            clause_id=finding.clause_id,
            severity=finding.severity,
            demo=demo_name,
        )
        for finding in analysis.findings
    ]


def collect_points(
    sources: list[tuple[AnalysisResult, set[str], str]],
) -> list[CalibrationPoint]:
    points: list[CalibrationPoint] = []
    for analysis, expected, name in sources:
        points.extend(_evaluate_one(analysis, expected, name))
    return points


def bin_points(
    points: list[CalibrationPoint],
    edges: tuple[float, ...] = DEFAULT_BIN_EDGES,
) -> list[CalibrationBin]:
    bins: list[CalibrationBin] = []
    for low, high in zip(edges[:-1], edges[1:]):
        bucket = [p for p in points if low <= p.confidence < high]
        if not bucket:
            bins.append(
                CalibrationBin(low=low, high=high, count=0, correct=0,
                               mean_confidence=(low + high) / 2, precision=0.0)
            )
            continue
        n = len(bucket)
        correct = sum(p.correct for p in bucket)
        mean_conf = sum(p.confidence for p in bucket) / n
        bins.append(
            CalibrationBin(
                low=low,
                high=high,
                count=n,
                correct=correct,
                mean_confidence=round(mean_conf, 3),
                precision=round(correct / n, 3),
            )
        )
    return bins


def build_report(points: list[CalibrationPoint]) -> CalibrationReport:
    if not points:
        return CalibrationReport(points=[], bins=[], overall_precision=0.0, brier=0.0, ece=0.0)

    n = len(points)
    overall = sum(p.correct for p in points) / n
    brier = sum((p.confidence - p.correct) ** 2 for p in points) / n
    bins = bin_points(points)
    ece = sum(
        (b.count / n) * abs(b.mean_confidence - b.precision)
        for b in bins
        if b.count > 0
    )
    return CalibrationReport(
        points=points,
        bins=bins,
        overall_precision=round(overall, 3),
        brier=round(brier, 4),
        ece=round(ece, 4),
    )


def run_default_calibration(data_dir: Path) -> CalibrationReport:
    """Build the calibration report from the bundled gold + held-out sets."""

    sources: list[tuple[AnalysisResult, set[str], str]] = []

    gold_path = data_dir / "gold_high_risk.json"
    if gold_path.exists():
        gold = json.loads(gold_path.read_text())
        doc_path = data_dir / gold["document"]
        analysis = analyze_contract(doc_path.read_text(), filename=doc_path.name)
        sources.append((analysis, set(gold["expected_clause_ids"]), "gold high-risk"))

    holdout_path = data_dir / "holdout_influencer_gold.json"
    if holdout_path.exists():
        holdout = json.loads(holdout_path.read_text())
        doc_path = data_dir / holdout["document"]
        analysis = analyze_contract(doc_path.read_text(), filename=doc_path.name)
        sources.append((analysis, set(holdout["expected_clause_ids"]), "held-out influencer"))

    return build_report(collect_points(sources))


def confusion(predicted: set[str], expected: set[str]) -> dict[str, set[str]]:
    return {
        "true_positive": predicted & expected,
        "false_positive": predicted - expected,
        "false_negative": expected - predicted,
    }


def evaluate_with_metrics(analysis: AnalysisResult, expected: set[str]) -> dict[str, float | int | list[str]]:
    predicted = {f.clause_id for f in analysis.findings}
    conf = confusion(predicted, expected)
    tp = len(conf["true_positive"])
    fp = len(conf["false_positive"])
    fn = len(conf["false_negative"])
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "expected": len(expected),
        "predicted": len(predicted),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "false_positive_ids": sorted(conf["false_positive"]),
        "false_negative_ids": sorted(conf["false_negative"]),
    }
