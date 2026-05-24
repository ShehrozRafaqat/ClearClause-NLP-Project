# ClearClause — Presentation & Viva Guide

**Group: Shehroz Ali (MSDSF25M012) · Arslan Ahmad (MSDSF25M001)**

This guide is the script for demoing ClearClause in a 5–10 minute sessional
or viva. It pairs each on-screen step with the NLP concept it shows, so an
examiner can connect the product to the underlying coursework.

---

## 0. Setup (do once before the viva)

```bash
cd /home/shehroz/Documents/MSDATAScience2ndSemester/NLP/NLP_FinalProject
/home/shehroz/Documents/genai-course/.venv/bin/streamlit run app.py --server.port 8502
```

Open <http://127.0.0.1:8502> in a browser. Maximise the window.
Run the tests in another terminal so you can show a green pass if asked:

```bash
/home/shehroz/Documents/genai-course/.venv/bin/python -m unittest discover -s tests
/home/shehroz/Documents/genai-course/.venv/bin/python evaluation.py
```

---

## 1. The pitch (30 seconds)

> ClearClause is an NLP-driven contract risk analyzer for freelancers and
> small businesses. The user uploads a contract; the system segments it,
> detects 17 categories of legally significant clauses with a hybrid regex
> plus TF-IDF pipeline, scores the document on a transparent 0–100 risk
> scale, explains every clause in plain English, benchmarks it against a
> fair-contract standard, and produces a prioritised negotiation checklist.
> Everything works offline; Groq is an optional polish layer.

---

## 2. Demo flow (3 minutes on screen)

### Step 1 — Load the high-risk demo
1. In the sidebar, click **High-risk freelance demo**.
2. Click **Analyze contract**.
3. The status panel shows the pipeline stages: parsing, clause extraction,
   optional LLM polish, retrieval index build.

> **What to say:** "The same pipeline runs whether the input is TXT, PDF, or
> DOCX. The status panel shows the four stages."

### Step 2 — Executive Dashboard
- Point out the **risk gauge** (100/100, Critical Risk).
- Point out the **verdict card** ("Do not sign in the current form").
- Point out the **dimensional radar** (Money, Ownership, Freedom, Disputes,
  Operations) — note how Freedom and Ownership are saturated.
- Point out the **ranked priority red flags** on the right.

> **What to say:** "The gauge is not a label classifier — it's a transparent
> confidence-weighted sum of adjusted clause weights, plus pressure bonuses
> for HIGH and MEDIUM concentrations. We can recalculate it by hand from the
> clause table."

### Step 3 — Clauses & Evidence
- Filter HIGH only.
- Expand "View source evidence" on the IP Ownership card.
- Then switch the view radio to **Inline redline** — show the full contract
  with HIGH spans in coral and MEDIUM in amber, all highlighted in place.

> **What to say:** "Every finding carries a matched regex term, a red-flag
> count, a balancing-language count, and a TF-IDF semantic score. The
> evidence snippet is the actual span from the contract, with the matched
> phrase as the centring anchor. The redline view stitches all of those
> spans back into the original document so a reviewer can see at a glance
> which paragraphs need attention."

### Step 4 — Negotiation Coach
- Walk through the first three checklist cards.
- Scroll to the **fair-contract benchmark** table.
- Read one "missing" row and explain why missing standard clauses matter.

> **What to say:** "Detection alone isn't useful for a freelancer. The
> Negotiation Coach turns every detected clause into concrete asks, and
> compares the contract against an industry-standard baseline so we can
> flag both bad wording *and* clauses the contract should have but doesn't."

### Step 5 — Ask the Document
- Click a suggested question (e.g. "Who owns the final source code?").
- Then type a free-form question, e.g. "What happens if the client misses an
  invoice?"

> **What to say:** "Q&A is grounded retrieval — TF-IDF cosine similarity over
> chunked paragraphs, with a small intent map that shortcuts to a detected
> clause when keywords match. Even without Groq, every answer cites the
> exact text the system found."

### Step 6 — Pipeline & Evaluation
- Show the diagnostics table.
- Show precision / recall / F1 = 1.00 on the gold set.
- Show the held-out influencer evaluation block (P=0.92, R=1.0, F1=0.96 —
  intentionally below the gold; the model false-positives `non_compete` on
  what is really a category-exclusivity clause).
- Show the four-demo score-spread block (90 → 85 → 80 → 53 → 25).
- Show the **confidence calibration** plot: mean confidence vs. empirical
  precision per bin, plus the Brier and ECE numbers.

> **What to say:** "We have a hand-curated gold set of 17 clause IDs on the
> high-risk demo where F1 is 1.00, but that's the optimistic number — we
> also tuned the catalog against this contract. The honest number is the
> held-out influencer agreement, which the catalog was not designed for;
> there F1 drops to 0.96 and the model produces one false positive
> (`non_compete` on a section that is really exclusivity). The score
> gradient across the four bundled demos confirms we don't saturate at
> 100 — every contract gets a distinct score band. The calibration plot
> shows the model is slightly under-confident: when it says 0.95 it is
> actually right 100% of the time."

### Step 7 — Export
- Download the **HTML report**, open it in a browser.
- Download the **negotiation pack** (Markdown), open it in any editor.

> **What to say:** "The HTML report is print-ready and includes the verdict,
> summary, benchmark, checklist, and findings — what you'd email to a
> client or your lawyer. The Markdown pack is the checklist version, ready
> to paste into an email."

### Step 8 — Compare to balanced demo
- Sidebar → **Balanced service agreement** → **Analyze contract**.
- Show the score drop from 100 to ~55, the verdict change, and the radar
  flattening out.

> **What to say:** "Same pipeline, no thresholds tuned per document. The
> system correctly identifies the balanced version as Review Carefully and
> drops the High-severity count to zero."

---

## 3. Questions you should expect

**Q: How does clause extraction actually work?**
> Three signals per (rule, section) pair: (a) regex pattern matches against
> a curated catalog, (b) red-flag and green-flag (balancing language)
> counters, (c) TF-IDF cosine similarity between the section text and the
> rule's prototype description. The three signals are combined into a
> confidence score; the best-scoring section per rule wins.

**Q: Why hybrid? Why not just an LLM?**
> Explainability and reliability. The regex catalog is the legal knowledge,
> human-readable and auditable. TF-IDF picks up paraphrased clauses without
> a generative model. Confidence and matched signals are surfaced directly
> in the UI. Groq is an optional polish layer that never replaces the
> evidence — it only rewrites the explanation text.

**Q: How is the risk score computed?**
> For each finding: `contribution = max(0, adjusted_weight + red_bonus −
> green_discount) × confidence_factor`. Then `score = min(100, Σ
> contributions + 3.5·high_count + 1.25·medium_count)`. Dimensional scores
> aggregate the same contributions by business area (money, ownership,
> freedom, disputes, operations) and normalise against a per-area cap.

**Q: How accurate is it?**
> On the gold high-risk demo: precision, recall, F1 all equal 1.00. The
> meaningful product metric is the separation between the high-risk and
> balanced demos — they differ by more than 40 score points, which means
> the system would not call a balanced contract "Critical Risk".

**Q: What happens without a Groq key?**
> Everything still works. The plain-English explanations and the executive
> summary fall back to deterministic templates. Q&A uses extractive
> retrieval. Only the "polish" of wording changes.

**Q: How does the Q&A avoid hallucination?**
> The offline mode is fully extractive — it returns either a detected
> clause's pre-written plain-English explanation or the most relevant
> contract chunk verbatim. When Groq is enabled, it is constrained to
> answer using only the retrieved chunks, with an explicit "cannot find"
> fallback in the system prompt.

**Q: What's the limit of this approach?**
> Hand-curated catalogs cap recall to clauses the developer thought of. We
> mitigate this with TF-IDF semantic matching against prototypes, but a
> production system would also train a clause classifier (BERT / Sentence
> Transformers) on a labelled corpus like CUAD. That extension is
> straightforward — the `nlp.py` module already exposes a clean
> `(rule, section) → confidence` interface that a learned model can plug
> into.

---

## 4. Talking points if asked to explain the code

- `clearclause/document_io.py` — TXT, PDF (pdfplumber), DOCX (python-docx)
  parsing into a unified `ParsedDocument` dataclass.
- `clearclause/catalog.py` — 17 `ClauseRule` definitions. Each rule has
  regex patterns, semantic prototypes, red/green flags, plain-English
  template, business impact, recommendation, fair-contract standard, and
  concrete negotiation actions.
- `clearclause/nlp.py` — `split_sections` (paragraph-block segmentation),
  `_semantic_scores` (TF-IDF cosine to prototypes), `_confidence` (combines
  all signals), `_adjusted_severity` (red/green flag-driven severity
  changes), `extract_clauses` (the orchestrator).
- `clearclause/scoring.py` — transparent risk score formula.
- `clearclause/qa.py` — chunked TF-IDF retriever with clause-intent
  shortcuts.
- `clearclause/negotiation.py` — produces the priority checklist, the
  fair-contract benchmark (including detection of *missing* standard
  clauses), and tailored discovery questions.
- `clearclause/summarizer.py` — deterministic executive summary and the
  verdict object used by the dashboard and the HTML report.
- `clearclause/reporting.py` — presentation-quality HTML report, CSV, and
  Markdown negotiation pack.

---

## 5. Backup if Streamlit fails

If the browser tab dies mid-demo, in another terminal run:

```bash
/home/shehroz/Documents/genai-course/.venv/bin/python evaluation.py
```

That prints the precision / recall / F1 and the separation check directly
to the terminal, which is sufficient to evidence the pipeline still works.

You can also run a single function in the REPL:

```python
from clearclause.nlp import analyze_contract
from pathlib import Path
text = Path("data/demo_high_risk_freelance_contract.txt").read_text()
a = analyze_contract(text, filename="demo.txt")
print(a.risk.score, a.risk.label, len(a.findings))
```

---

*Educational NLP project output. Not legal advice.*
