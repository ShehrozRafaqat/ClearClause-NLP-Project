from __future__ import annotations

import csv
import io
from pathlib import Path
import unittest

from clearclause.calibration import (
    build_report,
    collect_points,
    evaluate_with_metrics,
    run_default_calibration,
)
from clearclause.negotiation import (
    EXPECTED_CORE_CLAUSES,
    build_benchmark,
    build_checklist,
    suggested_questions,
)
from clearclause.nlp import analyze_contract
from clearclause.qa import ContractQA
from clearclause.redline import redline_html
from clearclause.reporting import (
    build_html_report,
    findings_csv,
    negotiation_markdown,
)
from clearclause.summarizer import build_verdict


ROOT = Path(__file__).resolve().parents[1]


class ClearClausePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.high_text = (ROOT / "data" / "demo_high_risk_freelance_contract.txt").read_text()
        self.balanced_text = (ROOT / "data" / "demo_balanced_service_agreement.txt").read_text()

    def test_high_risk_demo_detects_core_clauses(self):
        analysis = analyze_contract(self.high_text, filename="demo_high_risk_freelance_contract.txt")
        clause_ids = {finding.clause_id for finding in analysis.findings}

        self.assertGreaterEqual(analysis.risk.score, 75)
        for required in (
            "ip_ownership",
            "non_compete",
            "unlimited_liability",
            "unilateral_termination",
            "automatic_renewal",
        ):
            self.assertIn(required, clause_ids)

    def test_balanced_demo_scores_lower_than_high_risk_demo(self):
        high_analysis = analyze_contract(self.high_text, filename="high.txt")
        balanced_analysis = analyze_contract(self.balanced_text, filename="balanced.txt")

        self.assertGreater(high_analysis.risk.score, balanced_analysis.risk.score)
        self.assertGreater(
            high_analysis.risk.score - balanced_analysis.risk.score,
            20,
            "high-risk demo and balanced demo should be cleanly separated",
        )

    def test_offline_qa_uses_detected_clause(self):
        analysis = analyze_contract(self.high_text, filename="demo.txt")
        qa = ContractQA(analysis.document.text, analysis.findings)

        answer = qa.answer("Who owns the final source code?")
        self.assertGreater(answer.confidence, 0.5)
        self.assertIn("own", answer.text.lower())

    def test_offline_qa_handles_renewal_and_liability_intents(self):
        analysis = analyze_contract(self.high_text, filename="demo.txt")
        qa = ContractQA(analysis.document.text, analysis.findings)

        renewal = qa.answer("Does this contract automatically renew?")
        self.assertGreater(renewal.confidence, 0.5)

        liability = qa.answer("Is my liability capped?")
        self.assertGreater(liability.confidence, 0.5)

    def test_negotiation_checklist_is_priority_sorted(self):
        analysis = analyze_contract(self.high_text, filename="demo.txt")
        checklist = build_checklist(analysis.findings)

        self.assertTrue(checklist, "high-risk demo must produce checklist items")
        severities = ["HIGH", "MEDIUM", "LOW"]
        seen_severity_idx = -1
        for item in checklist:
            self.assertIn(item.severity, severities)
            self.assertGreaterEqual(severities.index(item.severity), seen_severity_idx)
            seen_severity_idx = severities.index(item.severity)
            self.assertTrue(item.actions)

    def test_benchmark_includes_status_and_missing_clauses(self):
        # The balanced demo intentionally omits a few standard clauses (e.g. arbitration),
        # so the benchmark must flag the missing ones.
        analysis = analyze_contract(self.balanced_text, filename="balanced.txt")
        rows = build_benchmark(analysis.findings)
        statuses = {row.status for row in rows}
        self.assertTrue(statuses.intersection({"fair", "concerning", "high-risk", "missing"}))

        detected_ids = {f.clause_id for f in analysis.findings}
        missing_titles = {row.title for row in rows if row.status == "missing"}
        # any expected core clause not detected must show up as missing
        from clearclause.catalog import RULE_BY_ID

        for clause_id in EXPECTED_CORE_CLAUSES:
            if clause_id not in detected_ids:
                self.assertIn(RULE_BY_ID[clause_id].title, missing_titles)

    def test_suggested_questions_target_detected_risks(self):
        analysis = analyze_contract(self.high_text, filename="demo.txt")
        questions = suggested_questions(analysis, limit=4)
        self.assertEqual(len(questions), 4)
        joined = " | ".join(questions).lower()
        # the demo contains non-compete, liability, and IP - at least one of those
        # topics should surface in the suggested questions
        self.assertTrue(any(keyword in joined for keyword in ("own", "liability", "compete", "terminate", "renew")))

    def test_html_report_contains_key_sections(self):
        analysis = analyze_contract(self.high_text, filename="demo.txt")
        report = build_html_report(analysis)
        for section in (
            "ClearClause",
            "Risk score",
            "Negotiation checklist",
            "Fair-contract benchmark",
            "Detected clauses",
            "verdict",
        ):
            self.assertIn(section.lower(), report.lower())

    def test_markdown_negotiation_pack_is_well_formed(self):
        analysis = analyze_contract(self.high_text, filename="demo.txt")
        md = negotiation_markdown(analysis)
        self.assertIn("# ClearClause Negotiation Pack", md)
        self.assertIn("Priority negotiation actions", md)
        self.assertIn("Discovery questions", md)

    def test_csv_export_is_parseable(self):
        analysis = analyze_contract(self.high_text, filename="demo.txt")
        csv_text = findings_csv(analysis.findings)
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        self.assertGreater(len(rows), 5)
        for row in rows:
            self.assertIn("Clause", row)
            self.assertIn("Risk", row)
            self.assertIn("Confidence", row)

    def test_verdict_severity_matches_score(self):
        analysis_high = analyze_contract(self.high_text, filename="demo.txt")
        analysis_low = analyze_contract(self.balanced_text, filename="balanced.txt")
        verdict_high = build_verdict(analysis_high.risk)
        verdict_low = build_verdict(analysis_low.risk)
        self.assertIn(verdict_high.css_class, {"CRITICAL", "HIGH"})
        self.assertIn(verdict_low.css_class, {"REVIEW", "LOW"})


class ClearClauseSaaSDemoTests(unittest.TestCase):
    def test_saas_demo_detects_renewal_and_indemnity(self):
        saas_path = ROOT / "data" / "demo_subscription_saas.txt"
        if not saas_path.exists():
            self.skipTest("SaaS demo not present")
        analysis = analyze_contract(saas_path.read_text(), filename=saas_path.name)
        clause_ids = {finding.clause_id for finding in analysis.findings}
        self.assertIn("automatic_renewal", clause_ids)
        self.assertIn("indemnification", clause_ids)
        self.assertGreater(analysis.risk.score, 40)


class ClearClauseScoreSpreadTests(unittest.TestCase):
    """The four bundled demos should populate distinct risk-score bands."""

    def _score(self, filename: str) -> int:
        path = ROOT / "data" / filename
        if not path.exists():
            self.skipTest(f"{filename} not present")
        analysis = analyze_contract(path.read_text(), filename=filename)
        return analysis.risk.score

    def test_score_no_longer_saturates_at_100(self):
        high_risk = self._score("demo_high_risk_freelance_contract.txt")
        saas = self._score("demo_subscription_saas.txt")
        # Both worst-case contracts must be below the absolute ceiling AND
        # distinguishable from each other after the score re-curve.
        self.assertLessEqual(high_risk, 96)
        self.assertLessEqual(saas, 96)
        self.assertGreaterEqual(high_risk, 78)
        self.assertGreaterEqual(saas, 78)
        self.assertNotEqual(high_risk, saas)

    def test_friendly_demo_lands_in_low_risk(self):
        score = self._score("demo_friendly_consulting_letter.txt")
        self.assertLess(score, 30, f"friendly letter must be Low Risk, got {score}")

    def test_full_score_gradient_is_monotone(self):
        high_risk = self._score("demo_high_risk_freelance_contract.txt")
        saas = self._score("demo_subscription_saas.txt")
        balanced = self._score("demo_balanced_service_agreement.txt")
        friendly = self._score("demo_friendly_consulting_letter.txt")
        scores = [high_risk, saas, balanced, friendly]
        self.assertEqual(scores, sorted(scores, reverse=True))


class ClearClauseHeldOutEvaluationTests(unittest.TestCase):
    def test_holdout_eval_runs_and_metrics_are_in_range(self):
        gold_path = ROOT / "data" / "holdout_influencer_gold.json"
        contract_path = ROOT / "data" / "holdout_influencer_agreement.txt"
        if not gold_path.exists() or not contract_path.exists():
            self.skipTest("held-out demo not present")

        import json
        gold = json.loads(gold_path.read_text())
        analysis = analyze_contract(contract_path.read_text(), filename=contract_path.name)
        metrics = evaluate_with_metrics(analysis, set(gold["expected_clause_ids"]))

        # The held-out demo is intentionally outside the catalog's tuning,
        # so we accept some imperfection but require strong coverage.
        self.assertGreaterEqual(metrics["recall"], 0.80)
        self.assertGreaterEqual(metrics["precision"], 0.70)
        self.assertGreater(metrics["f1"], 0.80)


class ClearClauseCalibrationTests(unittest.TestCase):
    def test_calibration_report_has_bins_and_metrics(self):
        report = run_default_calibration(ROOT / "data")
        self.assertGreater(len(report.points), 10)
        non_empty_bins = [b for b in report.bins if b.count > 0]
        self.assertGreaterEqual(len(non_empty_bins), 2)
        self.assertGreaterEqual(report.overall_precision, 0.8)
        # Brier on a well-engineered catalog should be < 0.25
        self.assertLess(report.brier, 0.25)
        # ECE should be a finite number between 0 and 1
        self.assertGreaterEqual(report.ece, 0.0)
        self.assertLessEqual(report.ece, 1.0)

    def test_high_confidence_bin_has_high_precision(self):
        report = run_default_calibration(ROOT / "data")
        high_bins = [b for b in report.bins if b.low >= 0.84 and b.count > 0]
        self.assertTrue(high_bins, "expected at least one high-confidence bin populated")
        # Findings with >= 0.85 confidence should be right almost all the time
        for bin_ in high_bins:
            self.assertGreaterEqual(bin_.precision, 0.85)


class ClearClauseRedlineTests(unittest.TestCase):
    def test_redline_emits_severity_classes(self):
        path = ROOT / "data" / "demo_high_risk_freelance_contract.txt"
        analysis = analyze_contract(path.read_text(), filename=path.name)
        html = redline_html(analysis.document.text, analysis.findings)
        self.assertIn("rl-HIGH", html)
        self.assertIn("rl-MEDIUM", html)
        # Snippet text should be embedded somewhere
        self.assertIn("irrevocably", html.lower())
        # The wrapper class is present
        self.assertIn("cc-redline", html)

    def test_redline_respects_severity_filter(self):
        path = ROOT / "data" / "demo_high_risk_freelance_contract.txt"
        analysis = analyze_contract(path.read_text(), filename=path.name)
        only_high = redline_html(analysis.document.text, analysis.findings, severities=("HIGH",))
        self.assertIn("rl-HIGH", only_high)
        self.assertNotIn("rl-MEDIUM", only_high)
        self.assertNotIn("rl-LOW", only_high)

    def test_redline_on_low_risk_demo_has_few_or_no_high_marks(self):
        path = ROOT / "data" / "demo_friendly_consulting_letter.txt"
        if not path.exists():
            self.skipTest("friendly demo not present")
        analysis = analyze_contract(path.read_text(), filename=path.name)
        html = redline_html(analysis.document.text, analysis.findings)
        # Low-risk demo should have no HIGH highlights
        self.assertNotIn("rl-HIGH", html)


if __name__ == "__main__":
    unittest.main()
