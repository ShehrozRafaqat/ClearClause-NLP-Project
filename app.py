"""
ClearClause – Main Streamlit Application
AI-Powered Contract Risk Analyzer for Freelancers & Professionals
"""
import time
import os
import sys

import streamlit as st
from dotenv import load_dotenv

# ── Must be first Streamlit call ──────────────────────────────────────────────
st.set_page_config(
    page_title="ClearClause | AI Contract Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()

# ── Ensure src is importable ──────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SAMPLE_CONTRACT
from src.parser import parse_document
from src.extractor import get_extractor
from src.scorer import calculate_risk, plot_risk_gauge

# ── THEME CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Dark canvas ── */
.stApp {
    background: #050c1a;
    background-image:
        radial-gradient(ellipse 80% 60% at 50% -20%, rgba(37,99,235,.25) 0%, transparent 60%);
    color: #e2e8f0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060f1f 0%, #0a1628 100%);
    border-right: 1px solid #1e3a6e40;
}
[data-testid="stSidebar"] * { color: #cbd5e1; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f8fafc !important; }

/* ── Headings ── */
h1 { font-size: 2.4rem !important; font-weight: 900 !important;
     background: linear-gradient(135deg, #60a5fa, #a78bfa);
     -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h2 { color: #f1f5f9 !important; font-weight: 700 !important; }
h3 { color: #cbd5e1 !important; font-weight: 600 !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: rgba(30,58,110,.3);
    border: 1px solid #1e3a6e60;
    border-radius: 12px;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricValue"]  { color: #f8fafc !important; font-size: 2rem !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"]  { color: #94a3b8 !important; font-size: .9rem !important; }

/* ── Primary button ── */
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%) !important;
    border: none !important; font-weight: 700 !important;
    border-radius: 10px !important; letter-spacing:.02em !important;
    transition: all .2s !important;
}
[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 0 24px #3b82f660 !important; transform: translateY(-1px) !important;
}
[data-testid="baseButton-secondary"] {
    background: rgba(30,58,110,.35) !important;
    border: 1px solid #1e3a6e !important;
    color: #93c5fd !important; border-radius: 10px !important; font-weight: 600 !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-weight: 600 !important; color: #64748b !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #60a5fa !important; border-bottom-color: #3b82f6 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: rgba(15,23,42,.5) !important;
    border: 1px solid #1e2d47 !important; border-radius: 8px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(30,58,110,.15) !important;
    border: 2px dashed #1e3a6e !important; border-radius: 12px !important;
}

/* ── Input / text fields ── */
[data-testid="stTextInput"] input {
    background: #0f1f38 !important; border: 1px solid #1e3a6e !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div { background: #3b82f6 !important; border-radius: 4px; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] { background: rgba(15,23,42,.4) !important; border-radius: 12px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a1628; }
::-webkit-scrollbar-thumb { background: #1e3a6e; border-radius: 6px; }

/* ── Clause cards (via html) ── */
.cc-card {
    background: rgba(15,23,42,.55);
    backdrop-filter: blur(12px);
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    transition: box-shadow .2s, transform .2s;
}
.cc-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,.5); transform: translateY(-2px); }
.cc-card.HIGH { border-left: 4px solid #ef4444; }
.cc-card.MEDIUM { border-left: 4px solid #f59e0b; }
.cc-card.LOW { border-left: 4px solid #10b981; }

.cc-title {
    font-size: 1rem; font-weight: 700; color: #f8fafc;
    display: flex; align-items: center; gap: 10px; margin-bottom: .5rem;
}
.cc-badge {
    font-size: .7rem; font-weight: 700; padding: .2rem .7rem;
    border-radius: 999px; text-transform: uppercase; letter-spacing: .05em;
}
.cc-badge.HIGH { background: rgba(239,68,68,.12); color: #fca5a5; border: 1px solid rgba(239,68,68,.25); }
.cc-badge.MEDIUM { background: rgba(245,158,11,.12); color: #fcd34d; border: 1px solid rgba(245,158,11,.25); }
.cc-badge.LOW { background: rgba(16,185,129,.12); color: #6ee7b7; border: 1px solid rgba(16,185,129,.25); }

.cc-why { color: #94a3b8; font-size: .88rem; margin-bottom: .75rem; line-height: 1.6; }

.cc-plain {
    background: rgba(37,99,235,.08);
    border-left: 3px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: .75rem 1rem; margin: .75rem 0;
    color: #e2e8f0; font-size: .92rem; line-height: 1.6;
}
.cc-plain strong { color: #93c5fd; font-size: .75rem; text-transform: uppercase; display: block; margin-bottom: 4px; }

.cc-note {
    font-size: .8rem; color: #64748b; margin-top: .5rem;
    padding-top: .5rem; border-top: 1px solid #1e293b;
}

/* ── Hero ── */
.hero-wrapper {
    text-align: center; padding: 2.5rem 1rem 2rem;
}
.hero-badge {
    display: inline-block; background: rgba(37,99,235,.15);
    border: 1px solid rgba(37,99,235,.4); color: #93c5fd;
    font-size: .78rem; font-weight: 600; letter-spacing: .12em;
    text-transform: uppercase; padding: .4rem 1.2rem;
    border-radius: 999px; margin-bottom: 1.5rem;
}
.hero-title {
    font-size: 3.2rem; font-weight: 900; line-height: 1.1; margin-bottom: 1rem;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f0abfc 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { font-size: 1.1rem; color: #64748b; max-width: 600px; margin: 0 auto 2rem; line-height: 1.6; }

/* ── Feature pills ── */
.features { display: flex; gap: .75rem; justify-content: center; flex-wrap: wrap; margin-top: 1rem; }
.feat {
    background: rgba(30,58,110,.25); border: 1px solid #1e3a6e;
    border-radius: 999px; padding: .35rem 1rem;
    font-size: .82rem; color: #93c5fd; font-weight: 500;
}

/* ── Stat bar ── */
.stat-bar {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin: 1.5rem 0;
}
.stat-item {
    background: rgba(30,58,110,.2); border: 1px solid #1e3a6e40;
    border-radius: 12px; padding: 1rem 1.25rem; text-align: center;
}
.stat-num { font-size: 2rem; font-weight: 800; color: #f8fafc; }
.stat-lbl { font-size: .8rem; color: #64748b; margin-top: .25rem; }

/* ── Divider ── */
.cc-divider { border: none; border-top: 1px solid #1e293b; margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = dict(
        doc_parsed=False, doc_text="", doc_meta={},
        clauses=[], risk_score=0, risk_cat="",
        summary="", rag=None, chat=[], analysed=False,
    )
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

_init()


def _reset():
    for k in ("doc_parsed","doc_text","doc_meta","clauses","risk_score",
              "risk_cat","summary","rag","chat","analysed"):
        del st.session_state[k]
    _init()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ ClearClause")
    st.markdown("<p style='color:#64748b;font-size:.85rem'>AI Contract Risk Analyzer</p>", unsafe_allow_html=True)
    st.markdown("---")

    groq_key = st.text_input(
        "🔑 Groq API Key",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        help="Free key at console.groq.com — needed for AI simplification & chat",
    )

    st.markdown("---")
    st.markdown("### 📄 Upload Contract")
    uploaded = st.file_uploader(
        "PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"],
        on_change=_reset,
    )

    st.markdown("---")
    if st.button("🎯 Load Demo Contract", use_container_width=True):
        _reset()
        st.session_state.doc_text   = SAMPLE_CONTRACT
        st.session_state.doc_meta   = {"filename": "demo_freelance_contract.txt", "word_count": len(SAMPLE_CONTRACT.split()), "pages": 2}
        st.session_state.doc_parsed = True
        st.rerun()

    st.markdown("---")
    st.markdown("""
<div style='font-size:.78rem; color:#475569; line-height:1.7'>
<strong style='color:#64748b'>How it works</strong><br>
① Upload your contract<br>
② Click Analyze<br>
③ Read the risk report<br>
④ Ask the AI questions<br><br>
<em>Your document never leaves your machine — all embeddings are in-memory.</em>
</div>
""", unsafe_allow_html=True)


# ── Parse uploaded file ───────────────────────────────────────────────────────
if uploaded and not st.session_state.doc_parsed:
    with st.spinner("Reading document…"):
        try:
            result = parse_document(uploaded, filename=uploaded.name)
            st.session_state.doc_text   = result["text"]
            st.session_state.doc_meta   = result
            st.session_state.doc_parsed = True
            st.rerun()
        except Exception as e:
            st.error(f"Could not read file: {e}")


# ════════════════════════════════════════════════════════════════════════════════
#  LANDING PAGE (no document)
# ════════════════════════════════════════════════════════════════════════════════
if not st.session_state.doc_parsed:
    st.markdown("""
<div class="hero-wrapper">
    <div class="hero-badge">Natural Language Processing · MS Data Science</div>
    <div class="hero-title">ClearClause</div>
    <p class="hero-sub">
        Upload a contract and our AI pipeline will instantly identify risky clauses,
        simplify legal jargon, score your document, and answer your questions —
        all powered by state-of-the-art NLP.
    </p>
    <div class="features">
        <span class="feat">🔍 Clause Extraction</span>
        <span class="feat">⚠️ Risk Classification</span>
        <span class="feat">💬 Plain-English Simplification</span>
        <span class="feat">📋 Document Summary</span>
        <span class="feat">🤖 RAG Chatbot</span>
        <span class="feat">📊 Risk Score</span>
    </div>
</div>
""", unsafe_allow_html=True)

    # How-it-works steps
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc in [
        (c1, "📤", "Upload", "Drop in any PDF, DOCX, or TXT contract file"),
        (c2, "🧠", "Analyze", "NLP pipeline identifies 14 legal clause types"),
        (c3, "📊", "Score", "0–100 risk gauge with color-coded flags"),
        (c4, "💬", "Ask", "Chat with your contract using RAG + Groq LLaMA3"),
    ]:
        with col:
            st.markdown(f"""
<div style="background:rgba(30,58,110,.2);border:1px solid #1e3a6e40;border-radius:14px;
            padding:1.5rem;text-align:center;height:100%">
    <div style="font-size:2rem;margin-bottom:.75rem">{icon}</div>
    <div style="font-weight:700;color:#f8fafc;margin-bottom:.5rem">{title}</div>
    <div style="color:#64748b;font-size:.85rem">{desc}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center;color:#334155;font-size:.85rem">
    Upload a file from the sidebar or click <strong style='color:#60a5fa'>Load Demo Contract</strong> to try it instantly.
    </div>""", unsafe_allow_html=True)
    st.stop()


# ════════════════════════════════════════════════════════════════════════════════
#  DOCUMENT LOADED — Analyze button
# ════════════════════════════════════════════════════════════════════════════════
meta = st.session_state.doc_meta
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    fname = meta.get("filename", "contract")
    st.markdown(f"### 📄 `{fname}`")
    st.markdown(f"<p style='color:#64748b;font-size:.85rem'>"
                f"{meta.get('word_count', '?')} words &nbsp;·&nbsp; "
                f"~{meta.get('pages', '?')} page(s) &nbsp;·&nbsp; "
                f"{meta.get('file_type','').upper() or 'TXT'}</p>",
                unsafe_allow_html=True)
with col_h2:
    if st.button("🔄 New Contract", use_container_width=True):
        _reset(); st.rerun()

if not st.session_state.analysed:
    st.markdown("---")
    st.markdown("""
<div style="background:rgba(37,99,235,.08);border:1px solid rgba(37,99,235,.25);
            border-radius:12px;padding:1.25rem 1.5rem;text-align:center">
    <div style="font-size:1.1rem;font-weight:600;color:#93c5fd;margin-bottom:.5rem">
        Ready to analyze this contract
    </div>
    <div style="color:#64748b;font-size:.88rem">
        The NLP pipeline will extract clauses, score risk, simplify legal language, and prepare the Q&A chatbot.
        A Groq API key is required for AI features.
    </div>
</div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔍  Analyze Contract", type="primary", use_container_width=True):
        if not groq_key:
            st.error("⚠️ Please enter your Groq API key in the sidebar first. Get one free at console.groq.com")
            st.stop()

        steps = [
            "Extracting clauses with NLP pipeline…",
            "Scoring risk levels…",
            "Simplifying legal jargon with LLaMA3…",
            "Generating document summary…",
            "Building RAG vector index for Q&A…",
            "Done! ✓",
        ]
        bar  = st.progress(0)
        stat = st.empty()

        # ── Step 1: Clause extraction
        stat.markdown(f"**{steps[0]}**")
        extractor = get_extractor()
        clauses   = extractor.extract(st.session_state.doc_text)
        st.session_state.clauses = clauses
        bar.progress(20)

        # ── Step 2: Risk score
        stat.markdown(f"**{steps[1]}**")
        score, cat = calculate_risk(clauses)
        st.session_state.risk_score = score
        st.session_state.risk_cat   = cat
        bar.progress(35)

        # ── Step 3 & 4: AI Engine (simplification + summary)
        stat.markdown(f"**{steps[2]}**")
        try:
            from src.ai_engine import AIEngine
            ai = AIEngine(api_key=groq_key)
            for c in clauses:
                if c.risk_level in ("HIGH", "MEDIUM"):
                    c.simplified = ai.simplify_clause(c)
            bar.progress(65)

            stat.markdown(f"**{steps[3]}**")
            st.session_state.summary = ai.summarize_document(st.session_state.doc_text)
        except Exception as e:
            st.warning(f"AI simplification skipped: {e}")
        bar.progress(80)

        # ── Step 5: RAG index
        stat.markdown(f"**{steps[4]}**")
        try:
            from src.rag_engine import RAGEngine
            rag = RAGEngine(st.session_state.doc_text, api_key=groq_key)
            rag.build_index()
            st.session_state.rag = rag
        except Exception as e:
            st.warning(f"Q&A engine skipped: {e}")
        bar.progress(100)

        stat.markdown(f"**{steps[5]}**")
        time.sleep(0.4)
        bar.empty(); stat.empty()
        st.session_state.analysed = True
        st.rerun()

    st.stop()


# ════════════════════════════════════════════════════════════════════════════════
#  RESULTS DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════
clauses    = st.session_state.clauses
score      = st.session_state.risk_score
category   = st.session_state.risk_cat
high_cnt   = sum(1 for c in clauses if c.risk_level == "HIGH")
med_cnt    = sum(1 for c in clauses if c.risk_level == "MEDIUM")
low_cnt    = sum(1 for c in clauses if c.risk_level == "LOW")

# ── Stat bar ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="stat-bar">
    <div class="stat-item">
        <div class="stat-num" style="color:{'#ef4444' if score>66 else '#f59e0b' if score>33 else '#10b981'}">{score}</div>
        <div class="stat-lbl">Risk Score</div>
    </div>
    <div class="stat-item">
        <div class="stat-num" style="color:#ef4444">{high_cnt}</div>
        <div class="stat-lbl">High Risk Clauses</div>
    </div>
    <div class="stat-item">
        <div class="stat-num" style="color:#f59e0b">{med_cnt}</div>
        <div class="stat-lbl">Medium Risk</div>
    </div>
    <div class="stat-item">
        <div class="stat-num" style="color:#10b981">{low_cnt}</div>
        <div class="stat-lbl">Low Risk</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Overview",
    f"⚠️  Clauses ({len(clauses)})",
    "💬  Ask ClearClause",
    "📋  Full Report",
])


# ══════════════ TAB 1 – OVERVIEW ══════════════════════════════════════════════
with tab1:
    col_gauge, col_summ = st.columns([1, 1.4])

    with col_gauge:
        st.markdown("#### Risk Score")
        fig = plot_risk_gauge(score, category)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Risk breakdown mini-chart
        if clauses:
            import plotly.graph_objects as go
            labels = ["High Risk", "Medium Risk", "Low Risk"]
            values = [high_cnt, med_cnt, low_cnt]
            colors = ["#ef4444", "#f59e0b", "#10b981"]
            donut = go.Figure(go.Pie(
                labels=labels, values=values,
                hole=.55, marker_colors=colors,
                textinfo="label+value",
                textfont_color="#f8fafc",
            ))
            donut.update_layout(
                showlegend=False, margin=dict(l=10,r=10,t=10,b=10),
                height=200, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})

    with col_summ:
        st.markdown("#### AI-Generated Summary")
        if st.session_state.summary:
            st.markdown(st.session_state.summary)
        else:
            st.info("Summary not available — Groq key may be missing.")

        st.markdown("<hr class='cc-divider'>", unsafe_allow_html=True)

        # Top risks callout
        high_clauses = [c for c in clauses if c.risk_level == "HIGH"]
        if high_clauses:
            st.markdown("#### 🚨 Top High-Risk Issues")
            for c in high_clauses[:4]:
                st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;padding:.6rem .9rem;
            background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.2);
            border-radius:8px;margin-bottom:.5rem">
    <span style="font-size:1.2rem">{c.icon}</span>
    <div>
        <div style="font-weight:600;color:#fca5a5;font-size:.9rem">{c.clause_type}</div>
        <div style="color:#64748b;font-size:.8rem">{c.why_it_matters[:90]}…</div>
    </div>
</div>""", unsafe_allow_html=True)


# ══════════════ TAB 2 – CLAUSES ══════════════════════════════════════════════
with tab2:
    # Filter bar
    fc1, fc2, fc3, fc4 = st.columns(4)
    show_high = fc1.checkbox("🔴 High Risk",   value=True)
    show_med  = fc2.checkbox("🟡 Medium Risk", value=True)
    show_low  = fc3.checkbox("🟢 Low Risk",    value=True)
    fc4.markdown(f"<div style='padding-top:.5rem;color:#64748b;font-size:.85rem'>{len(clauses)} total</div>",
                 unsafe_allow_html=True)

    level_map = {"HIGH": show_high, "MEDIUM": show_med, "LOW": show_low}
    visible = [c for c in clauses if level_map.get(c.risk_level, True)]

    if not visible:
        st.info("No clauses match your filter.")

    for c in visible:
        # Build card HTML
        plain_block = ""
        if c.simplified:
            plain_block = f"""
<div class="cc-plain">
    <strong>📝 Plain English:</strong>
    {c.simplified}
</div>"""

        html = f"""
<div class="cc-card {c.risk_level}">
    <div class="cc-title">
        <span>{c.icon}</span>
        {c.clause_type}
        <span class="cc-badge {c.risk_level}">{c.risk_level}</span>
    </div>
    <div class="cc-why">{c.why_it_matters}</div>
    {plain_block}
    <div class="cc-note">{c.standard_note}</div>
</div>"""
        st.markdown(html, unsafe_allow_html=True)

        with st.expander(f"View extracted legal text — confidence {c.confidence:.0%}"):
            st.code(c.snippet, language="text")

        st.markdown("")  # spacer


# ══════════════ TAB 3 – Q&A CHATBOT ══════════════════════════════════════════
with tab3:
    st.markdown("#### 💬 Ask ClearClause")
    st.markdown("<p style='color:#64748b;font-size:.88rem;margin-top:-.5rem'>"
                "Ask anything about your contract — answers are grounded only in the document text.</p>",
                unsafe_allow_html=True)

    # Suggested questions based on detected clauses
    high_types = [c.clause_type for c in clauses if c.risk_level == "HIGH"]
    suggestions = []
    if "IP Ownership / Work-for-Hire" in high_types:
        suggestions.append("Who owns the work I produce under this contract?")
    if "Non-Compete" in high_types:
        suggestions.append("Am I allowed to work for other clients in the same industry?")
    if "Unilateral Termination" in high_types:
        suggestions.append("Can the client fire me without giving a reason?")
    if "Automatic Renewal" in high_types:
        suggestions.append("Does this contract renew automatically? How do I cancel?")
    if "Indemnification" in high_types:
        suggestions.append("Would I be responsible for paying the client's legal fees?")
    if not suggestions:
        suggestions = ["What are my main obligations?", "When does this contract end?", "How am I paid?"]

    st.markdown("**💡 Suggested questions:**")
    sq_cols = st.columns(min(3, len(suggestions)))
    for i, q in enumerate(suggestions[:3]):
        if sq_cols[i].button(q, key=f"sq_{i}"):
            st.session_state.chat.append({"role": "user", "content": q})
            if st.session_state.rag:
                answer = st.session_state.rag.query(q)
                st.session_state.chat.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("---")

    # Chat history
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if user_q := st.chat_input("Ask about your contract…"):
        st.session_state.chat.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)

        if not st.session_state.rag:
            reply = "⚠️ Q&A engine is not available. Please ensure a valid Groq API key was provided during analysis."
        else:
            with st.chat_message("assistant"):
                with st.spinner("Searching contract…"):
                    reply = st.session_state.rag.query(user_q)
                st.markdown(reply)

        st.session_state.chat.append({"role": "assistant", "content": reply})


# ══════════════ TAB 4 – FULL REPORT ══════════════════════════════════════════
with tab4:
    st.markdown("#### 📋 Full Analysis Report")

    # Build downloadable HTML report
    risk_color = "#ef4444" if score > 66 else "#f59e0b" if score > 33 else "#10b981"
    rows = ""
    for c in clauses:
        badge_style = {
            "HIGH":   "background:#fee2e2;color:#dc2626",
            "MEDIUM": "background:#fef3c7;color:#d97706",
            "LOW":    "background:#dcfce7;color:#16a34a",
        }[c.risk_level]
        plain = c.simplified or "<em>(simplification not available)</em>"
        rows += f"""
<tr>
  <td><strong>{c.icon} {c.clause_type}</strong></td>
  <td><span style="{badge_style};padding:3px 10px;border-radius:999px;font-size:.75rem;font-weight:700">{c.risk_level}</span></td>
  <td style="font-size:.85rem">{c.why_it_matters}</td>
  <td style="font-size:.85rem;font-style:italic">{plain}</td>
</tr>"""

    report_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ClearClause Report</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;margin:0;padding:40px;background:#fff;color:#0f172a}}
  h1{{font-size:2rem;font-weight:900;color:#0a1628}}
  .score{{font-size:3.5rem;font-weight:900;color:{risk_color}}}
  table{{width:100%;border-collapse:collapse;margin-top:20px}}
  th{{background:#0a1628;color:#fff;padding:10px 14px;text-align:left;font-size:.85rem}}
  td{{padding:10px 14px;border-bottom:1px solid #e2e8f0;vertical-align:top}}
  tr:nth-child(even){{background:#f8fafc}}
  .summary{{background:#f0f9ff;border-left:4px solid #0284c7;padding:16px 20px;border-radius:4px;margin:20px 0}}
</style>
</head>
<body>
<h1>⚖️ ClearClause — Contract Analysis Report</h1>
<p>Document: <strong>{meta.get('filename','contract')}</strong> &nbsp;|&nbsp;
   Words: {meta.get('word_count','?')} &nbsp;|&nbsp; Generated: {time.strftime('%Y-%m-%d %H:%M')}</p>
<hr>
<h2>Overall Risk Score</h2>
<div class="score">{score} / 100</div>
<p><strong>{category}</strong> &nbsp;·&nbsp; {high_cnt} high-risk &nbsp;·&nbsp; {med_cnt} medium &nbsp;·&nbsp; {low_cnt} low</p>
<hr>
<h2>AI Summary</h2>
<div class="summary">{st.session_state.summary.replace(chr(10),'<br>') if st.session_state.summary else 'Not available.'}</div>
<hr>
<h2>Clause Analysis ({len(clauses)} clauses)</h2>
<table>
<thead><tr><th>Clause Type</th><th>Risk</th><th>Why It Matters</th><th>Plain-English Translation</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<hr>
<p style="font-size:.75rem;color:#94a3b8">Generated by ClearClause · Shehroz Ali (MSDSF25M012) · Arslan Ahmed (MSDSF25M001) · MS Data Science NLP Project</p>
</body></html>"""

    st.download_button(
        "⬇️  Download Full Report (HTML)",
        data=report_html,
        file_name=f"ClearClause_Report_{time.strftime('%Y%m%d_%H%M')}.html",
        mime="text/html",
        use_container_width=True,
    )

    st.markdown("---")

    # Show summary
    st.markdown("**AI Summary**")
    st.markdown(st.session_state.summary or "*Not available.*")
    st.markdown("---")

    # Show all clauses as table
    st.markdown("**Detected Clauses**")
    import pandas as pd
    df = pd.DataFrame([{
        "Clause": f"{c.icon} {c.clause_type}",
        "Risk": c.risk_level,
        "Confidence": f"{c.confidence:.0%}",
        "Why It Matters": c.why_it_matters,
    } for c in clauses])
    st.dataframe(df, use_container_width=True, hide_index=True)
