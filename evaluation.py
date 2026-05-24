"""ClearClause evaluation harness.

Runs the full NLP pipeline against the gold demo, the held-out influencer
contract, the score-spread sanity check, and the confidence calibration
report. Prints everything in a single readable block so a sessional viva can
show the system is more than a UI mockup.
"""

from __future__ import annotations

import json
from pathlib import Path

from clearclause.calibration import evaluate_with_metrics, run_default_calibration
from clearclause.nlp import analyze_contract


ROOT = Path(__file__).parent


def _evaluate(document_path: Path, expected: set[str]) -> dict:
    analysis = analyze_contract(document_path.read_text(), filename=document_path.name)
    metrics = evaluate_with_metrics(analysis, expected)
    return {
        "document": document_path.name,
        "analysis": analysis,
        **metrics,
    }


def _print_metrics(title: str, result: dict, expected_count: int) -> None:
    print(title)
    print("-" * len(title))
    print(f"Document : {result['document']}")
    print(f"Expected : {expected_count}")
    print(f"Predicted: {result['predicted']}")
    print(f"TP/FP/FN : {result['tp']} / {result['fp']} / {result['fn']}")
    print(f"Precision: {result['precision']:.3f}")
    print(f"Recall   : {result['recall']:.3f}")
    print(f"F1-score : {result['f1']:.3f}")
    fps = result.get("false_positive_ids") or []
    fns = result.get("false_negative_ids") or []
    print(f"FP ids   : {', '.join(fps) if fps else 'none'}")
    print(f"FN ids   : {', '.join(fns) if fns else 'none'}")
    print()


def main() -> None:
    print("ClearClause Pipeline Evaluation")
    print("================================\n")

    gold_path = ROOT / "data" / "gold_high_risk.json"
    gold = json.loads(gold_path.read_text())
    expected = set(gold["expected_clause_ids"])
    document_path = ROOT / "data" / gold["document"]
    high = _evaluate(document_path, expected)
    _print_metrics("Gold demo (high-risk contract, used to tune the catalog)", high, len(expected))

    holdout_path = ROOT / "data" / "holdout_influencer_gold.json"
    if holdout_path.exists():
        holdout = json.loads(holdout_path.read_text())
        h_expected = set(holdout["expected_clause_ids"])
        h_doc_path = ROOT / "data" / holdout["document"]
        h_result = _evaluate(h_doc_path, h_expected)
        _print_metrics(
            "Held-out demo (influencer contract, catalog was NOT tuned for this domain)",
            h_result,
            len(h_expected),
        )

    print("Score spread across all bundled demos")
    print("--------------------------------------")
    demos = [
        ("High-risk freelance", "demo_high_risk_freelance_contract.txt"),
        ("SaaS subscription   ", "demo_subscription_saas.txt"),
        ("Held-out influencer ", "holdout_influencer_agreement.txt"),
        ("Balanced agreement  ", "demo_balanced_service_agreement.txt"),
        ("Friendly letter     ", "demo_friendly_consulting_letter.txt"),
    ]
    scores: list[int] = []
    for label, name in demos:
        path = ROOT / "data" / name
        if not path.exists():
            continue
        a = analyze_contract(path.read_text(), filename=name)
        scores.append(a.risk.score)
        print(f"  {label} -> {a.risk.score:3d}/100  ({a.risk.label})")
    if len(scores) >= 2:
        spread_ok = scores == sorted(scores, reverse=True) and (scores[0] - scores[-1] > 40)
        print(
            f"Gradient: {'PASS' if spread_ok else 'WARN'} "
            f"(monotone decreasing with > 40-point spread)"
        )
    print()

    print("Confidence calibration (gold + held-out combined)")
    print("--------------------------------------------------")
    report = run_default_calibration(ROOT / "data")
    print(f"Overall precision          : {report.overall_precision:.3f}")
    print(f"Brier score                : {report.brier:.4f}  (0 = perfect)")
    print(f"Expected calibration error : {report.ece:.4f}  (0 = perfect)")
    print(f"Findings sampled           : {len(report.points)}\n")
    print("  bin            n   correct   mean_conf   empirical_precision")
    for b in report.bins:
        if b.count == 0:
            continue
        print(
            f"  [{b.low:.2f}, {b.high:.2f})"
            f"   {b.count:3d}     {b.correct:3d}        {b.mean_confidence:.3f}"
            f"              {b.precision:.3f}"
        )


if __name__ == "__main__":
    main()
