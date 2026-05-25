# ClearClause — Project Report

**AI-Powered Contract Risk Analyzer for Freelancers**

| | |
|---|---|
| **Course** | Natural Language Processing — MS Data Science |
| **Semester** | Spring 2026 |
| **Submission** | NLP Final Project Report |
| **Group** | Shehroz Ali (MSDSF25M012) · Arslan Ahmad (MSDSF25M001) |
| **Repository** | <https://github.com/ShehrozRafaqat/ClearClause-NLP-Project> |
| **Live demo** | `streamlit run app.py --server.port 8502` |

---

## 0. Executive Summary

ClearClause is a hybrid-NLP contract review system that helps freelancers and
small businesses understand legal contracts before they sign. The user uploads
a TXT, PDF or DOCX contract; the system segments it, detects 17 categories of
legally significant clauses, scores the document on a 0–100 scale, explains
every clause in plain English, benchmarks each clause against a fair-contract
standard, and coaches the user through the specific negotiation moves to make.
A retrieval-based Q&A module lets the user interrogate the contract, and a
one-click HTML report can be exported for sharing.

The report is organised in three parts. **Part 0** lays out the project
requirements and success criteria. **Part 1** describes the technical
architecture, the tools we used, and the evaluation we ran. **Part 2** is a
Y Combinator-style business plan covering the market opportunity, target
customer, competitive landscape, business model, go-to-market strategy and
scale roadmap.

The proof of concept is fully built and tested: 21/21 unit tests pass,
gold-set F1 = 1.00, held-out F1 = 0.96, and the system produces a meaningful
risk gradient across five demo contracts (90 → 85 → 80 → 53 → 25).

---

## Part 0 — Project Requirements

### 0.1 The problem we set out to solve

Freelancers and small businesses routinely sign multi-page legal contracts
they do not fully understand. The clauses that hurt them most — broad IP
assignment, unilateral termination, unlimited liability, indemnification,
non-compete and auto-renewal — are written in dense legal language that is
opaque to anyone without a law degree. Hiring a lawyer for every contract is
unaffordable for an independent contractor on a $500 project.

The result is a measurable harm: lost IP and portfolio rights, contracts
terminated with no payment for completed work, liability claims that exceed
the project fee, and post-engagement restrictions that block future income.

### 0.2 What ClearClause does, in one sentence

ClearClause reads a contract, finds the clauses that matter, scores how risky
they are, explains them in plain English, compares them to a fair-contract
standard, and tells the freelancer exactly what to ask for in negotiation.

### 0.3 Functional requirements

1. **Parse** TXT, PDF and DOCX contracts into clean, normalised text.
2. **Segment** the document into clause-level blocks.
3. **Detect** at least 15 categories of legally significant clauses with
   precision and recall ≥ 0.90 on a held-out test set.
4. **Score** each clause for severity (HIGH / MEDIUM / LOW / INFO) and produce
   a transparent 0–100 risk score for the whole document.
5. **Explain** each clause in plain English, including why it matters, the
   business impact, and a fair-contract recommendation.
6. **Benchmark** each detected clause against a fair-contract baseline and
   flag standard clauses that are missing.
7. **Coach** the user with a priority-sorted, copy-pasteable negotiation
   checklist tied to the actual risks in the contract.
8. **Answer questions** grounded in the contract text (no hallucination).
9. **Export** a presentation-quality HTML report, a clause-level CSV, and a
   Markdown negotiation pack for email follow-up.
10. **Run fully offline.** An optional Groq LLM layer may improve wording but
    must never be required.

### 0.4 Non-functional requirements

- **Explainable.** Every finding must be traceable to specific regex matches,
  red/green flag counts, and a semantic similarity score.
- **Fast.** End-to-end analysis of a 5,000-word contract should complete in
  under 2 seconds on a developer laptop.
- **Reproducible.** A clean clone + `pip install -r requirements.txt` +
  `streamlit run app.py` should reproduce the demo exactly.
- **Tested.** Unit tests cover the full pipeline, exports, Q&A, score spread,
  held-out evaluation, calibration, and redline rendering.
- **Presentation-ready.** The user-facing UI should look like a real product,
  not a class demo.

### 0.5 Success criteria

| Criterion | Target | Delivered |
|---|---|---|
| Clause categories detected | ≥ 15 | **17** |
| Gold-set precision | ≥ 0.90 | **1.00** |
| Gold-set recall | ≥ 0.90 | **1.00** |
| Held-out F1 | ≥ 0.85 | **0.96** |
| Unit tests | All pass | **21 / 21** |
| Risk-score spread across demos | ≥ 40 points | **65 points** (90 → 25) |
| Works without an API key | Yes | Yes |
| One-click report export | Yes | HTML + CSV + Markdown |

All target criteria are met or exceeded.

---

## Part 1 — Technical Architecture & Tools

### 1.1 High-level architecture

The pipeline has six discrete stages, each with a single responsibility and a
clean dataclass interface so the whole system is explainable end-to-end:

```
parse_document  →  clean_text  →  split_sections  →  extract_clauses
                                                       │
       calculate_risk  ←  ClauseFinding[]  ────────────┘
              │
              ▼
       build_summary  →  build_verdict
              │
              ▼
  build_checklist + build_benchmark + redline_html + ContractQA + build_html_report
```

Every transformation returns an immutable dataclass (`ParsedDocument`,
`Section`, `ClauseFinding`, `RiskProfile`, `AnalysisResult`), so the data
flow is auditable at any point.

### 1.2 The clause catalog

`clearclause/catalog.py` defines 17 `ClauseRule` objects covering five risk
dimensions:

| Dimension | Clauses |
|---|---|
| Money & Liability | Payment Terms, Unlimited Liability, Indemnification, Limitation of Liability |
| Ownership & IP | IP Ownership / Work-for-Hire, Confidentiality / NDA, Data Privacy / Security |
| Termination & Renewal | Unilateral Termination, Automatic Renewal |
| Work Freedom | Non-Compete, Exclusivity, Non-Solicitation |
| Disputes | Governing Law & Jurisdiction, Arbitration / Court Waiver |
| Operations | Scope, Acceptance & Revisions, Assignment / Change of Control, Effective Date & Term |

Each rule carries: regex patterns, semantic prototypes, red-flag and
green-flag terms, plain-English template, why-it-matters explanation,
business impact, fair-contract standard, and a list of concrete negotiation
actions. Adding a new clause type is a matter of appending a new
`ClauseRule` — the rest of the pipeline picks it up automatically.

### 1.3 Hybrid clause extraction

For every `(rule, section)` pair the system computes three signals:

1. **Regex pattern matches** against the rule's hand-curated patterns.
2. **TF-IDF semantic similarity** between the section text and the rule's
   prototype description, computed with `sklearn`'s `TfidfVectorizer` (ngrams
   1–2, English stop-words removed).
3. **Red/green flag counters** — short patterns that push severity up
   (e.g. `\bunlimited\b`) or down (e.g. `\bfees paid\b`).

These signals combine into a single explainable confidence score:

```
if matched_terms:
    confidence = 0.48 + pattern_strength + flag_strength + 0.42·semantic + title_bonus
else:
    confidence = min(0.72, 0.30 + semantic + title_bonus)  # only fires past a threshold
```

The best-scoring section per rule wins, and severity is then adjusted by the
red/green flag counts (e.g. ≥ 3 green flags with 0 red flags demotes a HIGH
to LOW).

### 1.4 Risk scoring with an exponential compression curve

The naive risk score is a confidence-weighted sum of adjusted clause weights
plus a small severity-count pressure bonus. A linear sum saturates very
quickly — every "bad" contract clipped to 100, and the gauge lost all
information at the high end.

We solved this with an exponential compression curve:

```
contribution = (weight + red_bonus − green_discount) × conf_factor
raw_total    = Σ contributions + 3.5·high_count + 1.25·medium_count

if raw_total ≤ 60:    score = round(raw_total)
else:                 score = round(60 + 36·(1 − exp(−(raw_total − 60) / 160)))
                       ⇒ asymptote ≈ 96
```

This preserves the linear behaviour in the lower half (so a 28/100 still
means "a few low-severity findings") and compresses the upper half so the
worst contracts are *distinguishable* from each other:

- High-risk freelance demo: 90 / 100 (Critical Risk)
- SaaS subscription: 85 / 100 (Critical Risk)
- Held-out influencer: 80 / 100 (Critical Risk)
- Balanced agreement: 53 / 100 (Review Carefully)
- Friendly consulting letter: 25 / 100 (Low Risk)

### 1.5 Document-grounded Q&A

`clearclause/qa.py` builds a TF-IDF retrieval index over ~950-character
overlapping paragraphs. When the user asks a question we run two layers in
order:

1. **Clause-intent shortcut.** A hand-curated keyword map for 17 topics
   (`"who owns the work"` → `ip_ownership`) maps the question to the
   corresponding detected `ClauseFinding`, and we return its pre-written
   plain-English explanation + the actual contract evidence.
2. **TF-IDF retrieval fallback.** If no intent matches, we return the most
   similar contract chunk verbatim, with a confidence score.

The offline mode is fully extractive — it never invents text. An optional
Groq layer wraps the retriever and answers using the retrieved chunks as
context, with an explicit "cannot find" fallback in the system prompt.

### 1.6 Negotiation coach + fair-contract benchmark

`clearclause/negotiation.py` turns the detected clauses into product output:

- **`build_checklist`** sorts every HIGH/MEDIUM finding by severity and
  confidence, then emits a numbered list of concrete negotiation actions.
- **`build_benchmark`** compares each detected clause to its fair-standard
  text and assigns a status (`fair` / `concerning` / `high-risk`). It also
  flags expected standard clauses that are missing from the contract.
- **`suggested_questions`** picks discovery questions tailored to the actual
  risks detected.

### 1.7 Inline redline view

`clearclause/redline.py` re-locates each finding's snippet inside the cleaned
document text and renders the full contract as HTML with severity-coloured
highlight spans. Overlapping spans are resolved in favour of the higher
severity. The output is wired into a "Redline view" toggle in the Streamlit
Clauses tab.

### 1.8 Confidence calibration

For an explainable NLP system the confidence number on each finding has to
actually correlate with whether the finding is correct, otherwise the number
is decoration. `clearclause/calibration.py` runs the gold + held-out demos
and reports:

- **Overall precision:** 0.966 across 29 findings
- **Brier score:** 0.053 (0 is perfect)
- **Expected calibration error:** 0.126 (slightly under-confident)
- **High-confidence bin (≥ 0.85):** 15 findings, all correct (precision = 1.00)

### 1.9 Tools used (off-the-shelf libraries and their role)

| Library | Role | Why we picked it |
|---|---|---|
| **Streamlit** | Interactive UI with custom CSS | Fastest way to build a polished interactive UI in Python; supports custom HTML for the redline view |
| **scikit-learn** | TF-IDF vectorisation + cosine similarity | Standard, deterministic, easy to explain in a viva |
| **Plotly** | Risk gauge, severity donut, dimensional radar, calibration chart | Interactive charts that match Streamlit's reactive model |
| **pdfplumber** | PDF parsing | Robust text-layer extraction on freelance contracts |
| **python-docx** | DOCX parsing | Reads paragraphs + tables; the standard Word library |
| **python-dotenv** | Optional Groq API key loading | Standard env-management pattern |
| **groq** (optional) | LLM polish layer for explanations + summary + chat | Cheapest fast-inference provider for Llama 3.1 |
| **python-pptx** | Generated the presentation deck (dev tool) | Programmatic slide build keeps typography consistent |

The pipeline itself is built on standard scikit-learn primitives (TF-IDF +
cosine similarity) and the Python regex module — no neural model is in the
critical path, which keeps the system fully offline-capable, deterministic
and explainable.

### 1.10 Evaluation results

We evaluate against two labelled contracts:

| Set | Description | Precision | Recall | F1 |
|---|---|---|---|---|
| **Gold** | High-risk freelance demo, used to tune the catalog | 1.000 | 1.000 | 1.000 |
| **Held-out** | Influencer marketing agreement, NOT used to tune | 0.917 | 1.000 | **0.957** |

The held-out F1 is the honest number — we report it openly alongside the
optimistic gold-set number. The single false positive on the held-out demo
is `non_compete`, fired on a section the contract calls "Category
Exclusivity"; in legal practice it could be argued either way, but we
labelled it as pure exclusivity to keep the test honest.

The 21-test unit suite covers the full pipeline, exports, Q&A intents,
benchmark + missing-clause detection, score spread, calibration, and the
redline renderer.

---

## Part 2 — Business Plan (Y Combinator perspective)

### 2.1 What is ClearClause?

> **ClearClause is contract review for the 1.5 billion people who can't afford
> a lawyer.** Upload any freelance, employment or service contract; in under
> two seconds we score the risk, flag the dangerous clauses, explain them in
> plain English, and tell you what to ask the other side to change.

### 2.2 The problem

Freelancers, gig workers, and small-business operators sign legal contracts
they do not fully understand. The clauses that hurt them most are predictable
and recurring:

- **IP assignment** that takes the freelancer's source code, templates and
  portfolio rights with no carve-outs.
- **Unilateral termination** that lets the client end the engagement on 7
  days' notice with no payment for completed work.
- **Unlimited liability** that creates personal financial exposure orders of
  magnitude larger than the project fee.
- **Auto-renewal** with a 90-day non-renewal window that locks the
  freelancer in by default.
- **Non-compete** clauses that block the freelancer's main source of income
  for 12–24 months post-engagement.

Today their options are:

1. **Hire a lawyer.** $200–$500 per contract review. Uneconomic for a $500
   project.
2. **Use a generic legal template service** (LegalZoom, Rocket Lawyer).
   Helpful for *drafting* their own contract, not for reviewing one a client
   sent them.
3. **Sign blind.** What most freelancers actually do.

ClearClause exists for option 4: a 60-second AI review that is good enough
to catch the clauses that matter.

### 2.3 Why now

Three converging trends make 2025–2026 the right moment to build this:

1. **The freelance economy is now structural, not cyclical.** Upwork's
   Freelance Forward 2024 study estimates 64 million Americans freelanced in
   2023 (38% of the US workforce). Globally, the gig economy is forecast to
   reach **$1.86 trillion by 2031**. Pakistan alone is the **4th largest
   freelance market** by gross earnings (Payoneer Global Gig Economy Index).
2. **NLP for legal text became practical and cheap.** Models like
   Sentence-Transformers and instruction-tuned LLMs handle clause-level
   classification at a quality that was impossible three years ago. The
   marginal cost per contract review dropped to fractions of a cent.
3. **Marketplaces want this layer.** Upwork, Fiverr and Toptal already invest
   in dispute-resolution tooling. A contract-clarity layer is a natural
   distribution partner story.

### 2.4 Market opportunity

| Tier | Definition | Size |
|---|---|---|
| **TAM** | All independent professionals globally who sign English-language contracts | **~150 million people** |
| **SAM** | English-speaking tech/creative freelancers in our launch geographies (Pakistan, India, Philippines, Bangladesh, EU, US) | **~30 million people** |
| **SOM (Year 1–2)** | Pakistani + South Asian tech freelancers reachable through community + content channels | **~2 million people** |

If we capture **1% of SOM at $9/month** (Pro tier), that is **~$2.16M ARR**
in Year 2 from a single launch geography. The B2B and marketplace API tiers
are upside.

### 2.5 Geography — phased launch

| Phase | Geography | Why this market | Channels |
|---|---|---|---|
| **Phase 1 (M0–6)** | Pakistan | Home market for the founders, 4th-largest freelance market globally, high local trust, low CAC | Local freelance communities, Facebook groups, university CS societies, LinkedIn |
| **Phase 2 (M6–12)** | India + Bangladesh + Philippines | English-speaking, large freelance bases, similar contract pain | Freelance YouTube channels, Reddit, Indie Hackers |
| **Phase 3 (M12–24)** | UK + EU + US gig workers | Higher willingness to pay, mature freelance unions | Freelancers Union partnerships, SEO content, paid acquisition once unit economics are proven |
| **Phase 4 (M24+)** | Multilingual (Urdu, Arabic, Spanish) | Underserved local-language markets | Local partner channels |

### 2.6 Target customer

Our **Year-1 ideal customer profile** is:

- **Who:** Pakistani / South-Asian software developer or designer aged 22–35,
  on Upwork / Fiverr / Toptal, earning $1k–$8k a month from international
  clients.
- **Pain:** Has signed at least one contract they regretted — typically lost
  IP rights, was non-paid after termination, or got locked into auto-renewal.
- **Tech-comfort:** High. Lives on GitHub, Discord, Reddit.
- **Willingness to pay:** $5–$15 / month for a tool that saves them from one
  bad contract.
- **Distribution:** Reachable through Pakistani freelance influencers,
  university CS clubs, LinkedIn freelancer communities.

### 2.7 Competitive landscape

| Competitor | Who it serves | Price | Why ClearClause wins |
|---|---|---|---|
| **LegalZoom / Rocket Lawyer** | Small business owners drafting docs | $40–$300/mo | We *review* the contract a client sent; they help you *draft* one. |
| **Lawgeex** | Enterprise legal teams | $10k+/yr | Enterprise B2B; not accessible to freelancers. |
| **Ironclad / LinkSquares / ContractPodAi** | Fortune 500 CLM | $50k–$500k/yr | Enterprise CLM, not a freelancer review tool. |
| **Harvey AI / Spellbook** | Law firms / in-house lawyers | $100s/seat/mo | Built for lawyers, not their clients. |
| **DocuSign Insight** | Mid-market contract analytics | $$$ | Analytics, not negotiation coaching. |
| **ChatGPT / generic LLM** | Anyone | Free–$20/mo | No clause catalog, no calibrated severity, no negotiation playbook, hallucinates on legal text. |

**The freelancer-friendly, affordable, explainable, fast space is empty.**

#### What makes us defensible

1. **Catalog as a moat.** Our 17-clause catalog with hand-curated red/green
   flag patterns and fair-contract standards is the result of careful
   research; it improves with every new contract reviewed.
2. **Explainability.** Every finding is traceable to specific regex matches,
   flag counts, and a semantic similarity score. We are *auditable*; black-
   box LLMs are not.
3. **Offline-capable.** ClearClause runs without sending the contract to any
   third-party API — a real privacy advantage for freelancers handling
   confidential client material.
4. **Negotiation playbook.** We don't just say "this is risky" — we tell the
   user what specific wording to ask for. That is the product differentiator
   examiners often miss.
5. **Calibrated confidence.** Our confidence numbers correlate with empirical
   precision (Brier 0.053). Most LLM tools cannot give you that.

### 2.8 Business model — how we make money

Three revenue streams, layered as the company scales:

1. **Freemium SaaS for individual freelancers.**
   - **Free:** 2 contract reviews per month, basic export.
   - **Pro ($9 / month):** Unlimited reviews, full negotiation pack, contract
     history, redline export.
   - **Team ($29 / month):** Up to 5 seats, shared contract library, basic
     CSV API.
2. **Marketplace API for freelance platforms.**
   - Per-contract usage-based pricing for Upwork / Fiverr / Toptal /
     PeoplePerHour to surface ClearClause's risk score on every contract
     uploaded to their platform.
   - Estimated **$0.20 per review** at scale.
3. **Enterprise tier for agencies + freelance unions.**
   - White-labelled deployment, multi-tenant, SSO, audit logs.
   - **$5,000–$25,000 / year** depending on seat count.

Initial focus is on revenue stream 1 (direct freelancer subscriptions) for
the first 12 months — it has the cleanest unit economics and the shortest
sales cycle.

#### Unit economics (Year-1 targets)

- **ARPU:** $9 / month
- **CAC (community-led):** ~$8 (Pakistani / South-Asian market)
- **Gross margin:** ~85% (offline pipeline + occasional Groq inference)
- **Payback period:** < 2 months
- **LTV (assuming 18-month average tenure):** ~$140
- **LTV/CAC:** ~17×

### 2.9 Go-to-market — initial customer base

#### Phase 1 (Months 0–6): community-led, founder-driven

- **Pakistani freelancer communities.** Direct outreach in Facebook groups
  (PFA — Pakistan Freelancers Association, Karachi Freelancers etc.) — give
  away 100 free Pro accounts in exchange for written feedback + a Loom video.
- **University CS societies.** Workshops at FAST, NUST, LUMS, COMSATS — every
  graduating computer-science student becomes a freelancer at some point.
- **Pakistani freelance YouTube + LinkedIn.** Partner with Pakistani
  freelance influencers (Hisham Sarwar, Sehar Naveed, etc.) for paid
  walkthroughs.
- **Indie Hackers + Reddit r/freelance + r/Upwork.** Launch posts with the
  free tier as the call-to-action.
- **Product Hunt launch** at the end of Month 3.

#### Phase 2 (Months 6–12): content-led

- **SEO content engine.** 30+ explainer articles ("what does this clause in
  your Upwork contract mean?"), each ending with a free analysis CTA.
- **Free shareable HTML reports.** Every report carries a small
  ClearClause badge — built-in viral coefficient.
- **Strategic partnerships.** Approach freelance platforms with our usage
  data, offer the marketplace API tier.

#### Phase 3 (Months 12–24): paid + B2B

- **Performance marketing** on LinkedIn (freelance professionals) and Reddit.
- **Enterprise outbound** to freelance unions, agencies, and law firms with
  freelance-heavy client bases.

### 2.10 Scale plan — MVP → full production

| Stage | Months | What we build | What we learn |
|---|---|---|---|
| **MVP** (where we are) | M0 | Streamlit app, 17-clause catalog, redline view, Q&A, exports. Fully offline. | Does the pipeline produce useful output on real freelance contracts? |
| **V1** | M1–3 | User accounts (Supabase), Stripe billing, contract history, email digest, basic admin dashboard. Multilingual UI scaffold (English + Urdu). | What's the conversion rate from free → Pro? |
| **V2** | M3–6 | Browser extension (highlight a contract in Gmail, get instant risk score), mobile-responsive web app, contract diff between two versions. | Where do freelancers actually encounter contracts? |
| **V3** | M6–12 | Marketplace API for Upwork / Fiverr partners, multi-tenant infrastructure, FastAPI service split from the Streamlit demo, vector-database upgrade (pgvector / Pinecone) for semantic clause matching. | Can we sign a marketplace partner? |
| **V4** | M12+ | Enterprise tier with SSO, audit logs, custom catalogs per industry, fine-tuned Sentence-Transformer model trained on a labelled freelance-contract corpus, multi-language clause catalogs (Urdu, Arabic, Spanish). | How does the catalog quality compare to a learned classifier? |

#### Technical scaling considerations

- The current Streamlit MVP is **a single Python process** that loads a
  ~1k-line regex catalog into memory. It comfortably handles thousands of
  reviews per day on a single VM.
- Beyond that, the pipeline splits cleanly into a stateless **FastAPI
  service** behind a CDN. The TF-IDF index can be precomputed per
  catalog version and cached.
- For the marketplace API tier we'll **fine-tune a Sentence-Transformer
  classifier** on CUAD (the publicly labelled contract corpus from the
  Atticus Project) to improve recall on unusual clause wordings. The
  existing rule-based catalog stays as the explainable / auditable fallback.
- **Privacy posture.** All paid tiers offer an "offline-only" mode where the
  contract never leaves the user's region. Enterprise can self-host.

### 2.11 Team

- **Shehroz Ali** — MS Data Science. Lead on the NLP pipeline, scoring,
  calibration, and the Streamlit UI. Owns the technical architecture.
- **Arslan Ahmad** — MS Data Science. Lead on the clause catalog research,
  fair-contract benchmark design, the evaluation harness, and the business
  plan / market analysis.

Both founders have first-hand experience with the freelance contract pain
the product solves — including signing contracts that they later wished they
hadn't.

### 2.12 Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| **A large LLM player (OpenAI, Anthropic) launches a general "contract reviewer"** that good-enoughs our value prop. | Medium | Defensive moat: hand-curated catalog, calibrated confidence, freelancer-specific UX, and the negotiation playbook. We're the niche depth player, not the horizontal incumbent. |
| **Freelancers don't pay** for a tool they can replicate with ChatGPT. | High | Position as the *trusted, calibrated, evidence-grounded* layer. Make the free tier generous enough that a Pro upgrade pays for itself with one bad contract avoided. |
| **Marketplace partners refuse to integrate** (they prefer to keep contract review in-house). | Medium | Direct-to-freelancer revenue is the primary line; partner API is upside. |
| **Legal liability** — what if our analysis is wrong and a freelancer signs based on our advice? | Medium | Clear "educational output, not legal advice" disclaimer (already shipped). T&Cs limit our liability. Pro tier offers an opt-in human lawyer review for an additional fee. |
| **Catalog coverage gaps** on contracts from new domains (creator agreements, gig contracts, etc.) | Low–Medium | The held-out evaluation already exercises this; we'll add a labelled corpus per new geography as we expand. The CUAD-trained classifier in V4 closes the long tail. |

---

## Closing

ClearClause is a working, tested, explainable NLP product that already meets
every functional and non-functional requirement we set for the project. The
17-clause catalog detects with F1 = 1.00 on the gold demo and F1 = 0.96 on a
genuinely held-out contract from a different domain. The risk score has a
defensible mathematical structure, distinguishes five demo contracts cleanly,
and the confidence numbers are empirically calibrated.

The business case is realistic: a large and growing freelance market, a
clear and underserved pain point, a credible launch geography for a
Pakistani-founded team, a multi-tier revenue model, and a phased
go-to-market that does not depend on any single channel.

The next sessional milestone is the live presentation, where we will walk
through the technical architecture and the business plan in 10–15 minutes
using the deck included in this submission (`ClearClause_Presentation.pptx`
and `ClearClause_Presentation.pdf`).

---

*Educational NLP project output. Not legal advice.*
