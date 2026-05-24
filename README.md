# ClearClause — AI Contract Risk Analyzer

> **NLP Final Project · MS Data Science**
>
> **Group members**
> - Shehroz Ali — `MSDSF25M012`
> - Arslan Ahmad — `MSDSF25M001`

ClearClause is a practical NLP system that analyzes freelance and professional
contracts. It segments the document, detects 17 categories of legally
significant clauses with a hybrid pipeline, scores the overall risk on a
0–100 scale, explains every clause in plain English, benchmarks each clause
against a fair-contract standard, and produces a prioritised negotiation
checklist. A retrieval Q&A module lets the user interrogate the contract,
and a presentation-quality HTML report can be exported in one click.

The project is fully offline-capable. A Groq API key is optional and only
polishes the wording of summaries, explanations, and chat answers.

> Educational NLP output. Not legal advice.

## Highlights

- **TXT / PDF / DOCX parsing** with paragraph normalisation and metadata.
- **Hybrid clause extraction** combining a curated regex catalog (17 clause
  types) with TF-IDF semantic similarity over clause prototypes.
- **Explainable risk score** with severity counts, dimensional breakdown
  (money, ownership, freedom, disputes, operations), an exponential-curve
  compression so worst-case contracts don't all saturate at 100, and a
  written verdict.
- **Executive dashboard** with a Plotly risk gauge, severity donut, business-
  area radar, category bar chart, and ranked priority red flags.
- **Inline redline view** — the full cleaned contract rendered with HIGH,
  MEDIUM and LOW clause spans highlighted in place, with hover tooltips.
- **Negotiation Coach** — every detected clause produces a checklist of
  concrete negotiation actions plus a fair-contract benchmark table.
- **Document-grounded Q&A** — TF-IDF retrieval over the contract chunks with
  clause-aware intent matching for the most common questions.
- **Optional Groq AI polish** for explanations, summaries, and answers.
- **One-click exports** — presentation-quality HTML report, clause CSV, and a
  Markdown "negotiation pack" ready to paste into an email.
- **Evaluation harness** with precision / recall / F1 on a gold demo, an
  honest held-out evaluation contract from a different domain, the score
  gradient across the full Critical → Low-Risk demo spectrum, and a
  confidence calibration report (Brier score + ECE + reliability bins).
- **Unit tests** covering the full pipeline, benchmark, exports, Q&A,
  scoring spread, held-out evaluation, calibration, and redline view.

## Quick start

```bash
git clone git@github.com:ShehrozRafaqat/ClearClause-NLP-Project.git
cd ClearClause-NLP-Project
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

Or, with the venv used during development:

```bash
cd /home/shehroz/Documents/MSDATAScience2ndSemester/NLP/NLP_FinalProject
/home/shehroz/Documents/genai-course/.venv/bin/streamlit run app.py --server.port 8502
```

Or:

```bash
./run.sh
```

Then open <http://127.0.0.1:8502>.

## Optional Groq setup

ClearClause works without an API key. To enable LLM polish:

```bash
cp .env.example .env
# then edit .env and set
# GROQ_API_KEY=your_key_here
```

When the key is present and the sidebar toggle is on, Groq rewrites the
plain-English explanations of HIGH/MEDIUM findings, regenerates the executive
summary, and answers chat questions using the offline retriever as context.

## Demo flow (60-second viva path)

1. From the sidebar, click **High-risk freelance demo**.
2. Click **Analyze contract**.
3. **Executive Dashboard** — show the gauge, the verdict card, the radar,
   and the ranked priority red flags.
4. **Clauses & Evidence** — filter by HIGH, expand "View source evidence"
   to show the matched span inside the contract.
5. **Negotiation Coach** — walk through the prioritised checklist and the
   fair-contract benchmark table (note the "missing" rows for clauses a
   balanced contract would normally cover).
6. **Ask the Document** — click a suggested question; show the offline
   retrieval answer.
7. **Pipeline & Evaluation** — show precision = recall = F1 = 1.0 on the gold
   set and the separation between high-risk and balanced demos.
8. **Export** — download the HTML report.

Compare against the **Balanced service agreement** demo to show the system
correctly drops the score and severity counts.

## Project structure

```text
ClearClause-NLP-Project/
├── app.py                          # Streamlit UI (6 tabs)
├── evaluation.py                   # precision / recall / F1 harness
├── run.sh
├── README.md
├── PRESENTATION_GUIDE.md           # viva script and talking points
├── clearclause/                    # the NLP pipeline package
│   ├── __init__.py
│   ├── ai.py                       # optional Groq integration
│   ├── calibration.py              # reliability bins + Brier + ECE
│   ├── catalog.py                  # 17 clause rules + fair standards
│   ├── document_io.py              # TXT / PDF / DOCX parsing
│   ├── models.py                   # dataclasses
│   ├── negotiation.py              # checklist + fair-contract benchmark
│   ├── nlp.py                      # regex + TF-IDF clause extraction
│   ├── qa.py                       # retrieval Q&A with clause intents
│   ├── redline.py                  # inline-highlight rendering
│   ├── reporting.py                # HTML / CSV / Markdown export
│   ├── scoring.py                  # 0–100 risk score (exponential curve)
│   └── summarizer.py               # summary + verdict card
├── data/
│   ├── demo_balanced_service_agreement.txt
│   ├── demo_friendly_consulting_letter.txt   # Low Risk demo (~25/100)
│   ├── demo_high_risk_freelance_contract.txt
│   ├── demo_subscription_saas.txt
│   ├── gold_high_risk.json
│   ├── holdout_influencer_agreement.txt      # held-out evaluation contract
│   └── holdout_influencer_gold.json
├── assets/
│   └── styles.css                  # polished LegalTech UI styling
├── docs/                           # academic proposal + supporting docs
│   ├── 04_Project_Proposal_YC_Technical_Perspective.{md,pdf,tex}
│   └── NLP_Project_Proposal.{md,tex}
└── tests/
    └── test_pipeline.py            # 21 unit tests
```

## Verification commands

```bash
/home/shehroz/Documents/genai-course/.venv/bin/python -m unittest discover -s tests
/home/shehroz/Documents/genai-course/.venv/bin/python evaluation.py
```

Expected output: **21 unit tests pass**; precision = recall = F1 = 1.00 on
the in-domain gold demo; held-out influencer demo F1 = 0.96; risk-score
gradient across the four bundled demos: **90 → 85 → 80 → 53 → 25**.

## NLP pipeline at a glance

```
parse_document  ─►  clean_text  ─►  split_sections (paragraph blocks)
        │
        ▼
extract_clauses  ─►  for every (rule, section):
                          regex pattern matches
                          red / green flag counts
                          TF-IDF cosine similarity to prototypes
                          confidence = f(patterns, flags, semantic, title)
                     keep the best-confidence section per rule
        │
        ▼
calculate_risk   ─►  confidence-weighted sum of adjusted weights
                     dimensional aggregation, severity counts, top flags
        │
        ▼
build_summary    ─►  parties, effective date, money, obligations, decision
        │
        ▼
ContractQA       ─►  TF-IDF chunk retrieval + clause-intent shortcuts
```

Optional layer: when a Groq API key is provided, the same `ClauseFinding`
objects are passed to `GroqAssistant.simplify_clause` and the document text
+ detected titles to `GroqAssistant.summarize`. The Q&A layer wraps the
offline retriever and calls `GroqAssistant.answer` with the retrieved chunks
as grounding context.

## Academic notes

- The detection layer is intentionally explainable: every finding can be
  traced back to a matched regex term, a red/green flag count, and a
  semantic similarity score. The dashboard surfaces all three on each
  clause card.
- The risk score is a transparent confidence-weighted sum, not a black-box
  classifier — important for a teaching context.
- The retrieval Q&A grounds every answer in actual contract evidence; the
  optional LLM layer never invents text outside the retrieved chunks.
