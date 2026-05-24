from __future__ import annotations

import html
import json
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from clearclause.ai import GroqAssistant
from clearclause.calibration import (
    CalibrationReport,
    evaluate_with_metrics,
    run_default_calibration,
)
from clearclause.catalog import DEFAULT_QUESTIONS
from clearclause.document_io import parse_document, parse_text
from clearclause.negotiation import (
    BenchmarkRow,
    NegotiationItem,
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
    findings_to_rows,
    negotiation_markdown,
)
from clearclause.summarizer import build_verdict


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"


st.set_page_config(
    page_title="ClearClause · Contract Risk Analyzer",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv(ROOT / ".env")


def load_css() -> None:
    css_path = ROOT / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


load_css()


# ----------------------------------------------------------------------------
# State helpers
# ----------------------------------------------------------------------------

def reset_analysis() -> None:
    for key in ("analysis", "qa", "chat", "source_name", "raw_text"):
        st.session_state.pop(key, None)


def analyze_current(groq_key: str, use_ai: bool) -> None:
    source_name = st.session_state.get("source_name", "contract.txt")
    raw_text = st.session_state.get("raw_text", "")
    if not raw_text.strip():
        st.error("Please upload, paste, or load a demo contract first.")
        return

    with st.status("Running ClearClause NLP pipeline...", expanded=True) as status:
        st.write("• Parsing and normalising document text")
        document = parse_text(raw_text, filename=source_name)

        st.write("• Detecting legal clauses (regex + TF-IDF semantic similarity)")
        analysis = analyze_contract(document)

        if use_ai and groq_key:
            assistant = GroqAssistant(api_key=groq_key)
            try:
                st.write("• Enhancing high/medium risk explanations with Groq")
                for finding in analysis.findings:
                    if finding.severity in {"HIGH", "MEDIUM"}:
                        finding.plain_english = assistant.simplify_clause(finding)
                st.write("• Generating AI executive summary")
                analysis.summary_markdown = assistant.summarize(
                    analysis.document.text,
                    [finding.title for finding in analysis.findings],
                )
            except Exception as exc:
                st.warning(f"AI enhancement skipped — falling back to deterministic output ({exc}).")

        st.write("• Building retrieval index for contract Q&A")
        st.session_state.analysis = analysis
        st.session_state.qa = ContractQA(analysis.document.text, analysis.findings)
        st.session_state.chat = []
        status.update(label="Analysis complete", state="complete", expanded=False)


def load_demo(path: Path) -> None:
    reset_analysis()
    st.session_state.raw_text = path.read_text()
    st.session_state.source_name = path.name


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------

def risk_gauge(score: int, label: str, color: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"font": {"size": 52, "color": color}, "suffix": "/100"},
            title={"text": f"<span style='font-size:14px;color:#5a6a62;text-transform:uppercase;letter-spacing:.14em'>{label}</span>", "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#8a958e", "tickfont": {"size": 11, "color": "#5a6a62"}},
                "bar": {"color": color, "thickness": 0.7},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 30], "color": "#d6f0df"},
                    {"range": [30, 60], "color": "#fdf3c6"},
                    {"range": [60, 78], "color": "#fee4d6"},
                    {"range": [78, 100], "color": "#f8c8b9"},
                ],
                "threshold": {
                    "line": {"color": "#1f3a2d", "width": 3},
                    "thickness": 0.85,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(
        height=290,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def severity_donut(analysis) -> go.Figure:
    labels = ["High", "Medium", "Low", "Info"]
    values = [
        analysis.risk.high_count,
        analysis.risk.medium_count,
        analysis.risk.low_count,
        analysis.risk.info_count,
    ]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker_colors=["#c2410c", "#b45309", "#15803d", "#1d4ed8"],
            textinfo="label+value",
            textfont={"size": 12, "color": "#0f1d18"},
            sort=False,
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font={"family": "Inter, sans-serif"},
        annotations=[
            dict(
                text=f"<b>{sum(values)}</b><br><span style='color:#5a6a62;font-size:11px;letter-spacing:.12em;text-transform:uppercase'>clauses</span>",
                x=0.5, y=0.5, font_size=22, showarrow=False,
            )
        ],
    )
    return fig


def dimension_radar(scores: dict[str, int]) -> go.Figure:
    labels = list(scores.keys()) or ["No data"]
    values = list(scores.values()) or [0]
    fig = go.Figure(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(47,90,64,.18)",
            line=dict(color="#2f5a40", width=2),
            marker=dict(size=7, color="#1f3a2d"),
            hovertemplate="%{theta}: %{r}/100<extra></extra>",
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=30, r=30, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            radialaxis=dict(range=[0, 100], tickfont={"size": 10, "color": "#5a6a62"}, gridcolor="#e3e6dd"),
            angularaxis=dict(tickfont={"size": 11, "color": "#243029"}, gridcolor="#e3e6dd"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        font={"family": "Inter, sans-serif"},
    )
    return fig


def calibration_chart(report: CalibrationReport) -> go.Figure:
    bins = [b for b in report.bins if b.count > 0]
    if not bins:
        return go.Figure()

    labels = [f"{b.low:.2f}–{b.high:.2f}" for b in bins]
    confidences = [b.mean_confidence for b in bins]
    precisions = [b.precision for b in bins]
    counts = [b.count for b in bins]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=confidences,
            name="Mean confidence",
            marker_color="#cfd9c4",
            marker_line=dict(color="#6f8d5c", width=1),
            text=[f"{c:.2f}" for c in confidences],
            textposition="outside",
            hovertemplate="bin %{x}<br>mean confidence: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=labels,
            y=precisions,
            name="Empirical precision",
            marker_color="#2f5a40",
            marker_line=dict(color="#1f3a2d", width=1),
            text=[f"{p:.2f} (n={n})" for p, n in zip(precisions, counts)],
            textposition="outside",
            hovertemplate="bin %{x}<br>precision: %{y:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        barmode="group",
        height=320,
        margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Confidence bin", color="#5a6a62"),
        yaxis=dict(title="", range=[0, 1.10], color="#5a6a62", gridcolor="#e3e6dd"),
        font={"family": "Inter, sans-serif"},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font={"size": 11}),
    )
    return fig


def category_bar(findings) -> go.Figure:
    from collections import Counter

    counter: Counter[str] = Counter()
    for finding in findings:
        counter[finding.category or "Other"] += 1
    if not counter:
        return go.Figure()
    labels = list(counter.keys())
    values = [counter[k] for k in labels]
    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker=dict(color="#2f5a40", line=dict(color="#1f3a2d", width=1)),
            text=values,
            textposition="outside",
            hovertemplate="%{y}: %{x} clauses<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(220, 38 * len(labels) + 60),
        margin=dict(l=10, r=30, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, color="#5a6a62"),
        yaxis=dict(showgrid=False, color="#243029"),
        font={"family": "Inter, sans-serif"},
    )
    return fig


# ----------------------------------------------------------------------------
# Layout pieces
# ----------------------------------------------------------------------------

def hero() -> None:
    st.markdown(
        """
<div class="cc-hero">
  <div class="cc-hero-row">
    <div class="cc-brand-block">
      <div class="cc-brand-mark">CC</div>
      <div>
        <div class="cc-brand-name">ClearClause</div>
        <div class="cc-brand-tag">AI Contract Risk Analyzer · Final NLP Build</div>
      </div>
    </div>
    <div class="cc-hero-meta">
      <span class="cc-chip">17 clause categories</span>
      <span class="cc-chip">Regex + TF-IDF hybrid</span>
      <span class="cc-chip">Offline Q&amp;A</span>
      <span class="cc-chip">Groq optional</span>
    </div>
  </div>
  <p class="cc-hero-subtitle">
    Upload an employment, freelance, NDA, service, or lease contract and ClearClause
    extracts the legally significant clauses, scores the document, explains the language
    in plain English, benchmarks each clause against a fair-contract standard, and
    coaches you through the specific negotiation moves to make before signing.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )


def kpi_strip(analysis) -> None:
    risk = analysis.risk
    verdict = build_verdict(risk)
    score_color = {
        "CRITICAL": "#9a1b0a",
        "HIGH": "#c2410c",
        "REVIEW": "#b45309",
        "LOW": "#15803d",
    }.get(verdict.css_class, "#1f3a2d")

    avg_conf = sum(f.confidence for f in analysis.findings) / max(1, len(analysis.findings))

    st.markdown(
        f"""
<div class="cc-strip">
  <div class="cc-tile accent-ink">
    <span class="label">Risk score</span>
    <span class="value" style="color:{score_color}">{risk.score}/100</span>
    <span class="hint">{html.escape(risk.label)}</span>
  </div>
  <div class="cc-tile accent-coral">
    <span class="label">High-risk clauses</span>
    <span class="value">{risk.high_count}</span>
    <span class="hint">Must-fix before signing</span>
  </div>
  <div class="cc-tile accent-amber">
    <span class="label">Medium-risk clauses</span>
    <span class="value">{risk.medium_count}</span>
    <span class="hint">Negotiate wording</span>
  </div>
  <div class="cc-tile accent-green">
    <span class="label">Low / Info</span>
    <span class="value">{risk.low_count + risk.info_count}</span>
    <span class="hint">Routine clauses</span>
  </div>
  <div class="cc-tile accent-forest">
    <span class="label">Avg confidence</span>
    <span class="value">{avg_conf:.0%}</span>
    <span class="hint">{analysis.document.word_count} words analysed</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def verdict_card(analysis) -> None:
    verdict = build_verdict(analysis.risk)
    st.markdown(
        f"""
<div class="cc-verdict {verdict.css_class}">
  <span class="verdict-label">ClearClause verdict</span>
  <div class="verdict-line">{html.escape(verdict.label)} — {html.escape(verdict.one_liner)}</div>
  <div class="verdict-body">{html.escape(verdict.body)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def top_red_flags(analysis) -> None:
    findings = [f for f in analysis.findings if f.severity == "HIGH"]
    findings.sort(key=lambda f: (-f.adjusted_weight, -f.confidence))
    findings = findings[:5]

    if not findings:
        st.markdown(
            "<div class='cc-panel'><span class='cc-panel-title'>Priority red flags</span>"
            "No high-severity clauses detected. Review the medium-risk items in the negotiation coach.</div>",
            unsafe_allow_html=True,
        )
        return

    rows = []
    for idx, finding in enumerate(findings, 1):
        rows.append(
            f"""
<div class="cc-flag">
  <div class="flag-title">
    <span>{html.escape(finding.title)}</span>
    <span class="flag-rank">#{idx}</span>
  </div>
  <div class="flag-impact">{html.escape(finding.business_impact or finding.why_it_matters)}</div>
</div>
"""
        )
    st.markdown(
        "<div class='cc-panel'><span class='cc-panel-title'>Priority red flags · ranked by business impact</span>"
        + "".join(rows)
        + "</div>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------

def sidebar() -> tuple[str, bool]:
    with st.sidebar:
        st.markdown(
            """
<div class="cc-sidebar-brand">
  <div class="mark">CC</div>
  <div>
    <div class="name">ClearClause</div>
    <div class="role">Final NLP Build</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='cc-side-step'><b>Step 1 · Source</b>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload contract", type=["txt", "pdf", "docx"], label_visibility="collapsed")
        if uploaded:
            try:
                parsed = parse_document(uploaded, filename=uploaded.name)
                st.session_state.raw_text = parsed.text
                st.session_state.source_name = uploaded.name
                st.success(f"Loaded {uploaded.name}")
            except Exception as exc:
                st.error(f"Could not parse file: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<div class='cc-side-step'><b>Demo contracts</b>"
            "<div style='font-size:.72rem;color:#5a6a62;margin:.1rem 0 .35rem 0'>"
            "Four demos covering Critical → Low Risk for full-spectrum testing.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Critical: High-risk freelance", use_container_width=True, key="demo_high"):
            load_demo(DATA_DIR / "demo_high_risk_freelance_contract.txt")
            st.rerun()
        saas_path = DATA_DIR / "demo_subscription_saas.txt"
        if saas_path.exists() and st.button(
            "Critical: SaaS subscription", use_container_width=True, key="demo_saas"
        ):
            load_demo(saas_path)
            st.rerun()
        holdout_path = DATA_DIR / "holdout_influencer_agreement.txt"
        if holdout_path.exists() and st.button(
            "Critical: Held-out influencer", use_container_width=True, key="demo_holdout"
        ):
            load_demo(holdout_path)
            st.rerun()
        if st.button("Review: Balanced agreement", use_container_width=True, key="demo_balanced"):
            load_demo(DATA_DIR / "demo_balanced_service_agreement.txt")
            st.rerun()
        friendly_path = DATA_DIR / "demo_friendly_consulting_letter.txt"
        if friendly_path.exists() and st.button(
            "Low: Friendly consulting letter", use_container_width=True, key="demo_friendly"
        ):
            load_demo(friendly_path)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Step 2 · Optional AI polish", expanded=False):
            groq_key = st.text_input(
                "Groq API key",
                value=os.getenv("GROQ_API_KEY", ""),
                type="password",
                help="Optional. Without a key, ClearClause still works fully offline.",
            )
            use_ai = st.checkbox("Use Groq for polished explanations", value=bool(groq_key))
            st.caption(
                "When enabled, Groq rewrites high/medium risk explanations and the executive "
                "summary. Q&A also uses Groq as a layer on top of the offline retriever."
            )

        st.markdown("<div class='cc-side-step'><b>Workspace</b>", unsafe_allow_html=True)
        if st.button("Reset workspace", use_container_width=True, key="reset"):
            reset_analysis()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        analysis = st.session_state.get("analysis")
        if analysis:
            risk = analysis.risk
            st.markdown(
                f"""
<div class='cc-side-step'>
<b>Live status</b>
<div style='font-size:.85rem;color:#243029;line-height:1.5'>
Score: <b>{risk.score}/100</b><br>
Findings: <b>{len(analysis.findings)}</b><br>
High / Med / Low: <b>{risk.high_count} / {risk.medium_count} / {risk.low_count}</b>
</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.caption("Educational NLP output — not legal advice.")
    return groq_key, use_ai


# ----------------------------------------------------------------------------
# Workspace
# ----------------------------------------------------------------------------

def input_workspace(groq_key: str, use_ai: bool) -> None:
    left, right = st.columns([1.2, 0.85], gap="large")
    with left:
        st.markdown(
            "<span class='cc-panel-title' style='display:block;margin-bottom:.35rem'>"
            "Contract workspace · paste or load a contract</span>",
            unsafe_allow_html=True,
        )
        default_text = st.session_state.get("raw_text", "")
        text = st.text_area(
            "Paste contract text",
            value=default_text,
            height=330,
            placeholder="Paste an employment, freelance, NDA, service, or lease agreement here...",
            label_visibility="collapsed",
        )
        st.session_state.raw_text = text
        if not st.session_state.get("source_name"):
            st.session_state.source_name = "pasted_contract.txt"

        analyze = st.button("Analyze contract", type="primary", use_container_width=True)
        if analyze:
            analyze_current(groq_key, use_ai)
            st.rerun()

    with right:
        ai_note = (
            "<b style='color:#2f5a40'>● Groq AI enabled</b> — polished summary and explanations"
            if groq_key and use_ai
            else "<b style='color:#5a6a62'>● Offline mode</b> — fully deterministic NLP pipeline"
        )
        st.markdown(
            f"""
<div class="cc-panel">
  <span class="cc-panel-title">What this demo shows</span>
  <ul style="margin:.2rem 0 .2rem 1.1rem;padding:0;color:#243029;line-height:1.55">
    <li>TXT / PDF / DOCX contract parsing and section segmentation</li>
    <li>Hybrid NLP: regex catalog + TF-IDF semantic similarity over 17 clause types</li>
    <li>Risk score, dimensional breakdown, and a presentation-quality verdict card</li>
    <li>Negotiation coach with fair-contract benchmark and prioritised checklist</li>
    <li>Offline retrieval Q&amp;A grounded in the uploaded contract</li>
    <li>HTML report, CSV findings, and markdown negotiation pack exports</li>
  </ul>
  <div style='margin-top:.65rem;font-size:.85rem'>{ai_note}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.info(
            "Fastest demo path: load the **High-risk freelance demo** from the sidebar, "
            "then click **Analyze contract**."
        )


# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------

def dashboard_tab(analysis) -> None:
    verdict_card(analysis)
    col1, col2 = st.columns([0.9, 1.1], gap="large")
    with col1:
        st.markdown(
            "<span class='cc-panel-title' style='display:block;margin-bottom:.3rem'>Composite risk score</span>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            risk_gauge(analysis.risk.score, analysis.risk.label, analysis.risk.tone),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown(
            "<span class='cc-panel-title' style='display:block;margin:.4rem 0 .3rem'>Clauses by severity</span>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(severity_donut(analysis), use_container_width=True, config={"displayModeBar": False})
    with col2:
        st.markdown(
            "<span class='cc-panel-title' style='display:block;margin-bottom:.3rem'>Risk by business area</span>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            dimension_radar(analysis.risk.dimension_scores),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown(
            "<span class='cc-panel-title' style='display:block;margin:.4rem 0 .3rem'>Detected clauses by category</span>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(category_bar(analysis.findings), use_container_width=True, config={"displayModeBar": False})

    st.markdown("")
    cols = st.columns([1.0, 1.0], gap="large")
    with cols[0]:
        top_red_flags(analysis)
    with cols[1]:
        st.markdown(
            "<div class='cc-panel'><span class='cc-panel-title'>Executive summary</span>"
            + analysis.summary_markdown.replace("\n", "  \n") +
            "</div>",
            unsafe_allow_html=True,
        )


def clause_card(finding) -> None:
    terms = ", ".join(finding.matched_terms) or "semantic match"
    red = ", ".join(finding.red_flags) or "None"
    green = ", ".join(finding.green_flags) or "None"
    category_chip = (
        f"<span class='badge-soft'>{html.escape(finding.category)}</span>" if finding.category else ""
    )
    st.markdown(
        f"""
<div class="clause-card {finding.severity}">
  <div class="clause-title">
    <span>{html.escape(finding.title)}</span>
    <span><span class="badge {finding.severity}">{finding.severity} · {finding.confidence:.0%}</span></span>
  </div>
  <div class="clause-meta">{category_chip}<span class='badge-soft'>{html.escape(finding.section_title)}</span></div>
  <div class="clause-body">
    <b>Plain English.</b> {html.escape(finding.plain_english)}
  </div>
  <div class="clause-grid">
    <div class="cell"><b>Why it matters</b><span>{html.escape(finding.why_it_matters)}</span></div>
    <div class="cell"><b>Business impact</b><span>{html.escape(finding.business_impact)}</span></div>
    <div class="cell"><b>Recommendation</b><span>{html.escape(finding.recommendation)}</span></div>
    <div class="cell"><b>Matched signal</b><span>terms: {html.escape(terms)}<br>red flags: {html.escape(red)}<br>balancing: {html.escape(green)}</span></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.expander("View source evidence in the contract"):
        st.markdown(
            f"<div class='evidence'>{html.escape(finding.snippet)}</div>",
            unsafe_allow_html=True,
        )


def clauses_tab(analysis) -> None:
    mode = st.radio(
        "View",
        ["Clause cards", "Inline redline"],
        horizontal=True,
        label_visibility="collapsed",
        key="clauses_view_mode",
    )

    if mode == "Inline redline":
        st.markdown(
            "<span class='cc-panel-title' style='display:block;margin:.1rem 0 .5rem'>"
            "Inline redline · full contract with HIGH and MEDIUM risk spans highlighted</span>",
            unsafe_allow_html=True,
        )
        sev_cols = st.columns([0.2, 0.2, 0.2, 0.4])
        include_high = sev_cols[0].checkbox("HIGH", value=True, key="rl_high")
        include_medium = sev_cols[1].checkbox("MEDIUM", value=True, key="rl_med")
        include_low = sev_cols[2].checkbox("LOW", value=False, key="rl_low")
        severities = tuple(
            sev
            for sev, include in (("HIGH", include_high), ("MEDIUM", include_medium), ("LOW", include_low))
            if include
        ) or ("HIGH",)
        html_content = redline_html(analysis.document.text, analysis.findings, severities=severities)
        st.markdown(html_content, unsafe_allow_html=True)
        st.caption(
            "Hover over any highlight to see which clause it belongs to. Spans are located by "
            "snippet match, so very short or paraphrased snippets may be skipped."
        )
        return

    c1, c2, c3, c4, c5 = st.columns([0.18, 0.18, 0.18, 0.18, 0.28])
    show_high = c1.checkbox("High", value=True, key="card_high")
    show_medium = c2.checkbox("Medium", value=True, key="card_med")
    show_low = c3.checkbox("Low", value=True, key="card_low")
    show_info = c4.checkbox("Info", value=False, key="card_info")
    search = c5.text_input(
        "Search clause titles", "", label_visibility="collapsed", placeholder="Search titles…"
    )

    allowed = {
        "HIGH": show_high,
        "MEDIUM": show_medium,
        "LOW": show_low,
        "INFO": show_info,
    }
    visible = [
        finding
        for finding in analysis.findings
        if allowed.get(finding.severity, True)
        and (not search or search.lower() in finding.title.lower())
    ]
    if not visible:
        st.info("No findings match the selected filters.")
        return
    for finding in visible:
        clause_card(finding)


def negotiation_tab(analysis) -> None:
    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin-bottom:.35rem'>"
        "Prioritised negotiation checklist · ranked by severity and confidence</span>",
        unsafe_allow_html=True,
    )
    checklist = build_checklist(analysis.findings)
    if not checklist:
        st.success(
            "No high or medium-severity clauses with actionable language were detected. "
            "Review the low-risk clauses for routine wording cleanups."
        )
    for item in checklist:
        actions_html = "".join(f"<li>{html.escape(a)}</li>" for a in item.actions)
        st.markdown(
            f"""
<div class="cc-checklist {item.severity}">
  <div class="cc-checklist-header">
    <span>#{item.priority} · {html.escape(item.title)}</span>
    <span><span class="rank">{html.escape(item.category)}</span> <span class="badge {item.severity}">{item.severity} · {item.confidence:.0%}</span></span>
  </div>
  <div class="rationale">{html.escape(item.rationale)}</div>
  <ul>{actions_html}</ul>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin:1rem 0 .35rem'>"
        "Fair-contract benchmark · detected language vs. industry standard</span>",
        unsafe_allow_html=True,
    )
    rows = build_benchmark(analysis.findings)
    if not rows:
        st.info("Benchmark data unavailable — no clauses detected.")
        return
    render_benchmark_table(rows)

    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin:1rem 0 .35rem'>"
        "Suggested questions tailored to the detected risks</span>",
        unsafe_allow_html=True,
    )
    questions = suggested_questions(analysis, limit=6)
    items = "".join(f"<li>{html.escape(q)}</li>" for q in questions)
    st.markdown(
        f"<div class='cc-panel'><ul style='margin:.1rem 0 .1rem 1.1rem'>{items}</ul></div>",
        unsafe_allow_html=True,
    )


def render_benchmark_table(rows: list[BenchmarkRow]) -> None:
    table_rows = []
    for row in rows:
        table_rows.append(
            f"<tr>"
            f"<td><strong>{html.escape(row.title)}</strong><br>"
            f"<small style='color:#5a6a62'>{html.escape(row.category)}</small></td>"
            f"<td><span class='bench-status {row.status}'>{row.status}</span></td>"
            f"<td>{html.escape(row.fair_standard)}</td>"
            f"<td>{html.escape(row.detected_text)}</td>"
            f"<td>{html.escape(row.gap)}</td>"
            f"</tr>"
        )
    table_html = (
        "<table class='cc-bench'><thead><tr>"
        "<th>Clause</th><th>Status</th><th>Fair standard</th>"
        "<th>Detected in this contract</th><th>Gap / action</th>"
        "</tr></thead><tbody>" + "".join(table_rows) + "</tbody></table>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def chat_tab(analysis, groq_key: str) -> None:
    qa = st.session_state.get("qa")
    if qa is None:
        qa = ContractQA(analysis.document.text, analysis.findings)
        st.session_state.qa = qa

    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin-bottom:.4rem'>"
        "Ask the document · grounded retrieval Q&amp;A</span>",
        unsafe_allow_html=True,
    )

    questions = suggested_questions(analysis, limit=6) or list(DEFAULT_QUESTIONS)
    cols = st.columns(min(3, len(questions)))
    for idx, question in enumerate(questions[:3]):
        if cols[idx % len(cols)].button(question, key=f"suggested_{idx}", use_container_width=True):
            st.session_state.chat.append({"role": "user", "content": question})
            answer = qa.answer(question)
            final = _finalize_answer(answer.text, question, groq_key, qa)
            st.session_state.chat.append({"role": "assistant", "content": final})
            st.rerun()

    for msg in st.session_state.get("chat", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask about payment, ownership, termination, liability, or future work")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching the contract..."):
                offline_answer = qa.answer(prompt)
                final_answer = _finalize_answer(offline_answer.text, prompt, groq_key, qa, offline_answer.sources)
                st.markdown(final_answer)
        st.session_state.chat.append({"role": "assistant", "content": final_answer})


def _finalize_answer(offline_text: str, question: str, groq_key: str, qa: ContractQA, sources: list[str] | None = None) -> str:
    if not groq_key:
        return offline_text
    try:
        assistant = GroqAssistant(api_key=groq_key)
        ctx_sources = sources if sources is not None else [chunk for chunk, _ in qa.retrieve(question, top_k=3)]
        context = "\n\n---\n\n".join(ctx_sources) if ctx_sources else offline_text
        return assistant.answer(question, context)
    except Exception:
        return offline_text


def evaluation_tab(analysis) -> None:
    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin-bottom:.35rem'>Pipeline diagnostics</span>",
        unsafe_allow_html=True,
    )
    diag_df = pd.DataFrame([analysis.diagnostics])
    st.dataframe(diag_df, use_container_width=True, hide_index=True)

    eval_data = run_full_evaluation()
    gold = eval_data["gold"]
    holdout = eval_data["holdout"]
    spread = eval_data["spread"]

    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin:.6rem 0 .35rem'>"
        "Gold demo · catalog was tuned against this contract</span>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precision", f"{gold['precision']:.2f}")
    c2.metric("Recall", f"{gold['recall']:.2f}")
    c3.metric("F1-score", f"{gold['f1']:.2f}")
    c4.metric("Expected clauses", gold["expected"])

    if holdout is not None:
        st.markdown(
            "<span class='cc-panel-title' style='display:block;margin:.7rem 0 .35rem'>"
            "Held-out demo · creator / influencer contract the catalog was NOT tuned against</span>",
            unsafe_allow_html=True,
        )
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Precision", f"{holdout['precision']:.2f}")
        d2.metric("Recall", f"{holdout['recall']:.2f}")
        d3.metric("F1-score", f"{holdout['f1']:.2f}")
        d4.metric("Expected clauses", holdout["expected"])
        if holdout.get("false_positive_ids") or holdout.get("false_negative_ids"):
            fp = ", ".join(holdout.get("false_positive_ids") or []) or "none"
            fn = ", ".join(holdout.get("false_negative_ids") or []) or "none"
            st.caption(f"Held-out FP: {fp}  ·  FN: {fn}")

    if spread is not None:
        st.markdown(
            f"""
<div class='cc-panel muted' style='margin-top:.4rem'>
  <span class='cc-panel-title'>Score discrimination across all four demos</span>
  <div style='display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.6rem;margin-top:.4rem'>
    <div><b style='color:#9a1b0a'>{spread['high_risk_score']}</b> &nbsp;<small>High-risk freelance</small></div>
    <div><b style='color:#c2410c'>{spread['saas_score']}</b> &nbsp;<small>SaaS subscription</small></div>
    <div><b style='color:#b45309'>{spread['balanced_score']}</b> &nbsp;<small>Balanced agreement</small></div>
    <div><b style='color:#15803d'>{spread['friendly_score']}</b> &nbsp;<small>Friendly letter</small></div>
  </div>
  <div style='margin-top:.45rem;font-size:.85rem;color:#5a6a62'>
    The model produces a meaningful score gradient — no two demos saturate at the same value.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin:.9rem 0 .35rem'>"
        "Confidence calibration · do the model's confidence numbers actually mean something?</span>",
        unsafe_allow_html=True,
    )
    calib_cols = st.columns([1.4, 1.0])
    with calib_cols[0]:
        st.plotly_chart(
            calibration_chart(eval_data["calibration"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    with calib_cols[1]:
        report = eval_data["calibration"]
        st.markdown(
            f"""
<div class='cc-panel muted'>
  <span class='cc-panel-title'>Calibration metrics</span>
  <div style='line-height:1.6;font-size:.92rem'>
    Overall precision: <b>{report.overall_precision:.3f}</b><br>
    Brier score: <b>{report.brier:.4f}</b> <small>(lower is better)</small><br>
    Expected calibration error: <b>{report.ece:.4f}</b><br>
    Findings sampled: <b>{len(report.points)}</b>
  </div>
  <div style='margin-top:.5rem;font-size:.85rem;color:#5a6a62'>
    For each confidence bin the bar shows the model's mean confidence next to
    the empirical precision actually observed. A well-calibrated model has the
    two bars at roughly equal height in every bin.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin:.9rem 0 .35rem'>"
        "Per-clause results · sortable table for the currently analysed contract</span>",
        unsafe_allow_html=True,
    )
    rows = findings_to_rows(analysis.findings)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown(
        """
<div class='cc-panel muted'>
  <span class='cc-panel-title'>Methodology recap for viva</span>
  <ol style='margin:.2rem 0 .2rem 1.1rem;padding:0;line-height:1.55'>
    <li>Document text is normalised, split into sections, and re-joined into chunks.</li>
    <li>Each section is scored against every clause rule using regex pattern matching.</li>
    <li>TF-IDF cosine similarity adds a semantic signal when patterns don't fire.</li>
    <li>Red-flag and balancing-language counters adjust severity and weight per clause.</li>
    <li>Raw risk is a confidence-weighted sum of adjusted weights, then passed through an
        exponential compression curve so the worst contracts don't all saturate at 100.</li>
    <li>Q&amp;A retrieves contract chunks and reuses detected clauses where intents match.</li>
  </ol>
</div>
""",
        unsafe_allow_html=True,
    )


def export_tab(analysis) -> None:
    html_report = build_html_report(analysis)
    csv_report = findings_csv(analysis.findings)
    md_report = negotiation_markdown(analysis)

    st.markdown(
        "<span class='cc-panel-title' style='display:block;margin-bottom:.35rem'>"
        "Presentation-ready exports</span>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.download_button(
        "Download HTML report",
        data=html_report,
        file_name="clearclause_contract_report.html",
        mime="text/html",
        use_container_width=True,
        help="Print-ready HTML with verdict, summary, benchmark, checklist, and findings.",
    )
    c2.download_button(
        "Download clause CSV",
        data=csv_report,
        file_name="clearclause_clause_findings.csv",
        mime="text/csv",
        use_container_width=True,
        help="Spreadsheet of every detected clause with severity, confidence, and evidence.",
    )
    c3.download_button(
        "Download negotiation pack (Markdown)",
        data=md_report,
        file_name="clearclause_negotiation_pack.md",
        mime="text/markdown",
        use_container_width=True,
        help="Copy-and-paste checklist for a follow-up email to the other party.",
    )

    with st.expander("Preview HTML report"):
        st.components.v1.html(html_report, height=620, scrolling=True)

    with st.expander("Preview negotiation pack"):
        st.markdown(md_report)

    st.markdown(
        """
<div class='cc-panel muted' style='margin-top:.7rem'>
  <span class='cc-panel-title'>Viva talking points</span>
  <ol style='margin:.2rem 0 .2rem 1.1rem;padding:0;line-height:1.55'>
    <li>Parser handles TXT, PDF, and DOCX; the same downstream pipeline runs in all cases.</li>
    <li>Clause detection is hybrid: explainable regex catalog + TF-IDF semantic prototypes.</li>
    <li>Each finding has severity, confidence, source evidence, and a negotiation action list.</li>
    <li>Risk score has a transparent formula (confidence-weighted adjusted weights + flag pressure).</li>
    <li>Q&amp;A is grounded retrieval: it returns contract evidence, not free-form generation.</li>
    <li>Groq is strictly an optional polish layer — the demo works fully offline.</li>
  </ol>
</div>
""",
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def run_full_evaluation() -> dict:
    """Run gold + held-out + spread + calibration. Cached so the tab is instant."""

    out: dict = {"gold": {}, "holdout": None, "spread": None}

    gold_path = DATA_DIR / "gold_high_risk.json"
    if gold_path.exists():
        gold = json.loads(gold_path.read_text())
        doc_path = DATA_DIR / gold["document"]
        analysis_gold = analyze_contract(doc_path.read_text(), filename=doc_path.name)
        metrics_gold = evaluate_with_metrics(analysis_gold, set(gold["expected_clause_ids"]))
        out["gold"] = metrics_gold
        out["gold_score"] = analysis_gold.risk.score

    holdout_path = DATA_DIR / "holdout_influencer_gold.json"
    if holdout_path.exists():
        holdout = json.loads(holdout_path.read_text())
        doc_path = DATA_DIR / holdout["document"]
        analysis_holdout = analyze_contract(doc_path.read_text(), filename=doc_path.name)
        out["holdout"] = evaluate_with_metrics(analysis_holdout, set(holdout["expected_clause_ids"]))
        out["holdout_score"] = analysis_holdout.risk.score

    spread: dict[str, int | None] = {
        "high_risk_score": None,
        "saas_score": None,
        "balanced_score": None,
        "friendly_score": None,
    }
    paths = {
        "high_risk_score": "demo_high_risk_freelance_contract.txt",
        "saas_score": "demo_subscription_saas.txt",
        "balanced_score": "demo_balanced_service_agreement.txt",
        "friendly_score": "demo_friendly_consulting_letter.txt",
    }
    for key, filename in paths.items():
        path = DATA_DIR / filename
        if path.exists():
            a = analyze_contract(path.read_text(), filename=filename)
            spread[key] = a.risk.score
    if any(v is not None for v in spread.values()):
        out["spread"] = spread

    out["calibration"] = run_default_calibration(DATA_DIR)
    return out


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    groq_key, use_ai = sidebar()
    hero()
    input_workspace(groq_key, use_ai)

    analysis = st.session_state.get("analysis")
    if not analysis:
        return

    kpi_strip(analysis)
    tabs = st.tabs(
        [
            "Executive Dashboard",
            "Clauses & Evidence",
            "Negotiation Coach",
            "Ask the Document",
            "Pipeline & Evaluation",
            "Export",
        ]
    )
    with tabs[0]:
        dashboard_tab(analysis)
    with tabs[1]:
        clauses_tab(analysis)
    with tabs[2]:
        negotiation_tab(analysis)
    with tabs[3]:
        chat_tab(analysis, groq_key)
    with tabs[4]:
        evaluation_tab(analysis)
    with tabs[5]:
        export_tab(analysis)

    st.markdown(
        "<div class='cc-footer'>ClearClause Final NLP Build · educational output, not legal advice.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
