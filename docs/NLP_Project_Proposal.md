# NLP Project Proposal

**Course:** Natural Language Processing — Final Project
**Program:** MS Data Science
**Submission Date:** April 2026

---

## Group Members

| Name | Student ID | Responsibility |
|------|-----------|----------------|
| **Shehroz Ali** | MSDSF25M012 | NLP Pipeline, Model Integration & Evaluation |
| **Arslan Ahmed** | MSDSF25M001 | System Design, UI/Demo & Business Analysis |

---

## Project Name

# ClearClause
### *AI-Powered Contract Risk Analyzer for Freelancers & Professionals*

---

## Project Description

### The Problem

Every day, millions of freelancers, fresh graduates, employees, and small business owners sign contracts they do not fully understand. Employment agreements, NDAs, freelance service contracts, and rental leases are routinely drafted by lawyers to protect the drafting party — heavily loaded with legal jargon, one-sided clauses, and hidden obligations. The average person has no way to identify what is risky, what is non-standard, or what rights they may be unknowingly waiving.

Pakistan alone is ranked **4th globally in freelancers**, with over **4 million registered freelancers** earning through platforms like Fiverr, Upwork, and Freelancer.com. These individuals regularly accept client contracts, intellectual property transfer agreements, and platform terms that can significantly affect their livelihood — yet no affordable tool exists to help them understand what they sign.

### The Solution

**ClearClause** is an intelligent NLP-powered contract analysis system that:

1. 🔍 **Extracts and identifies** key legal clauses from uploaded documents (PDF/DOCX)
2. ⚠️ **Classifies clause risk** — flagging dangerous, unusual, or one-sided terms (e.g., unlimited liability, automatic renewal, unilateral termination)
3. 💬 **Simplifies every clause** into plain, jargon-free English
4. 📋 **Summarizes** the full document in under 300 words with a structured key-points breakdown
5. 🤖 **Answers questions** about the document through a conversational AI interface
6. 📊 **Scores** the overall document on a 0–100 fairness / risk scale

ClearClause transforms complex legal language into immediate, actionable understanding — making it as easy to understand a contract as it is to read an email.

---

## Technical Perspective

### System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      CLEARCLAUSE SYSTEM                      │
│                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────┐  │
│  │  User Upload │────▶│     Document Ingestion Layer     │  │
│  │  (PDF/DOCX)  │     │  (pdfplumber + python-docx)      │  │
│  └──────────────┘     └────────────┬─────────────────────┘  │
│                                    │                         │
│                    ┌───────────────┼──────────────┐          │
│                    ▼               ▼              ▼          │
│          ┌──────────────┐  ┌──────────────┐ ┌──────────┐   │
│          │ Clause       │  │ Text         │ │  RAG     │   │
│          │ Extraction & │  │ Simplifica-  │ │  Q&A     │   │
│          │ Risk Classif.│  │ tion Engine  │ │  Engine  │   │
│          │ (Legal-BERT) │  │ (Groq LLM)   │ │(LangChain│   │
│          └──────┬───────┘  └──────┬───────┘ │+ FAISS)  │   │
│                 │                 │         └────┬─────┘   │
│                 └─────────────────┼──────────────┘         │
│                                   ▼                         │
│                     ┌─────────────────────────┐            │
│                     │   Risk Scoring Engine   │            │
│                     │   (Weighted Formula)    │            │
│                     └─────────────────────────┘            │
│                                   │                         │
│                                   ▼                         │
│                     ┌─────────────────────────┐            │
│                     │   Streamlit Web App UI  │            │
│                     │   (Interactive Report)  │            │
│                     └─────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

---

### Module Breakdown

#### Module 1 — Document Ingestion

- **Input:** PDF / DOCX contract file
- **Libraries:** `pdfplumber`, `python-docx`
- **Process:** Extract raw text → normalize whitespace → split into sentence-level chunks for downstream NLP
- **Output:** Clean text corpus chunked at paragraph/sentence level

---

#### Module 2 — Clause Extraction & Risk Classification (Core NLP Module)

This is the primary NLP task and academic contribution of the system.

- **Approach:** Extractive Question Answering (QA) framing over the document using a Legal-domain transformer model pre-trained on the **CUAD (Contract Understanding Atticus Dataset)**
- **Model Used:** `tomasonjo/deberta-v3-base-cuad` — publicly available on Hugging Face, fine-tuned on 13,000+ expert-annotated legal clauses across 41 risk categories
- **Clause Categories Detected (sample):**

  | Category | Risk Level |
  |----------|-----------|
  | Unlimited/All-or-Nothing Liability | 🔴 HIGH |
  | Automatic Renewal | 🔴 HIGH |
  | Unilateral Termination | 🔴 HIGH |
  | Non-Compete / Non-Solicitation | 🟡 MEDIUM |
  | Governing Law | 🟡 MEDIUM |
  | IP Ownership / Work-for-Hire | 🔴 HIGH |
  | Arbitration | 🟡 MEDIUM |
  | Indemnification | 🔴 HIGH |
  | Termination for Convenience | 🟡 MEDIUM |
  | Payment Terms | 🟢 LOW |

- **Technique:** Each clause category is posed as a QA query; the model performs span extraction to identify whether and where each clause exists in the document
- **Output:** A structured list of detected clauses, their textual spans, and assigned risk levels

---

#### Module 3 — Plain-English Simplification

- **Technique:** Instruction-tuned Large Language Model (LLM) via API, prompted to act as a legal plain-language translator
- **Model:** Groq API (`llama3-8b-8192` — free tier, ultra-fast inference, <1s latency)
- **Prompt Design:**
  ```
  You are a legal language simplifier. Rewrite the following contract clause 
  in plain English (max 2 sentences) that a non-lawyer can understand. 
  Do not change the legal meaning. 
  Clause: [EXTRACTED_CLAUSE_TEXT]
  ```
- **Why Groq over OpenAI:** Free tier, no rate limits for demo scale, sufficient quality for clause-level simplification
- **Output:** Plain English translation for every extracted high/medium-risk clause

---

#### Module 4 — Conversational Document Q&A (RAG Pipeline)

- **Architecture:** Retrieval-Augmented Generation (RAG)
- **Pipeline Steps:**
  1. Document chunks embedded via `sentence-transformers` (`all-MiniLM-L6-v2`)
  2. Embeddings stored in `FAISS` vector index (in-memory, no database needed)
  3. On user query → semantic search → top K relevant chunks retrieved
  4. Chunks + query passed to Groq LLM → grounded, document-specific answer generated
- **Framework:** LangChain `RetrievalQA` chain
- **Example interactions:**
  - *"Can the client fire me without reason?"*
  - *"Am I allowed to work for other clients?"*
  - *"Who owns my work after completion?"*
- **Output:** Conversational AI that answers questions using exclusively the uploaded contract as its knowledge source

---

#### Module 5 — Abstractive Document Summarization

- **Input:** All extracted and simplified clause texts + full document text
- **Technique:** Prompted LLM summarization (same Groq endpoint, zero additional cost)
- **Prompt:** Structured to produce a fixed-format report with sections: *Key Obligations, Rights Granted, Key Risks, Important Dates/Deadlines*
- **Output:** Structured bullet-point summary under 300 words

---

#### Module 6 — Risk Scoring Engine

- **Formula:**
  ```
  Risk Score = (HIGH_count × 30 + MEDIUM_count × 15 + LOW_count × 5) 
               normalized to 0–100 scale, capped at 100
  ```
- **Output:** Color-coded score: `0–33 🟢 Safe` / `34–66 🟡 Review Carefully` / `67–100 🔴 High Risk`
- **Display:** Gauge chart in Streamlit UI (using `plotly`)

---

### Datasets

| Dataset | Use Case | Status |
|---------|----------|--------|
| **CUAD** (Contract Understanding Atticus Dataset) | Pre-trained QA model for clause extraction | ✅ Pre-trained model available on HuggingFace |
| **TOS;DR** (Terms of Service Didn't Read) | Evaluation of simplification quality | ✅ Publicly available |
| **LEDGAR** (SEC legal provision dataset) | Additional clause variety for testing | ✅ Available via HuggingFace datasets |
| **Sample Freelance Contracts** (collected manually) | Demo and evaluation | ✅ Will collect 10–15 sample contracts |

> **Note:** We use pre-trained models throughout. No model training from scratch is required, significantly reducing compute cost and time while maintaining high accuracy on the legal domain.

---

### Technology Stack

| Layer | Tool | Justification |
|-------|------|---------------|
| NLP Backbone | `DeBERTa-v3` (CUAD-finetuned) | State-of-the-art legal clause QA |
| LLM API | Groq (`llama3-8b-8192`) | Free, fast (700 tokens/sec), sufficient quality |
| Embeddings | `sentence-transformers` | Efficient semantic search |
| Vector Search | FAISS | In-memory, no infra setup needed |
| RAG Framework | LangChain | Industry standard, well-documented |
| Document Parsing | `pdfplumber`, `python-docx` | Handles both PDF and Word formats |
| Web Interface | Streamlit | Rapid prototyping, Python-native |
| Visualization | `plotly` | Interactive charts in Streamlit |
| Language | Python 3.10+ | Team proficiency, ecosystem |

---

### Evaluation Metrics

| Module | Metric | Baseline |
|--------|--------|---------|
| Clause Extraction (QA) | F1-Score, Exact Match (EM) | CUAD benchmark: reported 87%+ F1 |
| Risk Classification | Accuracy, Macro-F1 | Evaluated on held-out CUAD clauses |
| Summarization | ROUGE-1/2/L | Evaluated against reference summaries |
| Simplification | Flesch-Kincaid Readability Improvement | Original vs. simplified clause reading level |
| Q&A Faithfulness | BERTScore vs. document source | Checks answer is grounded in document |

---

### 4-Day Prototype Development Plan

| Day | Shehroz Ali | Arslan Ahmed |
|-----|-------------|--------------|
| **Day 1** | Document ingestion pipeline + CUAD model integration for clause extraction | Set up project repo, Streamlit boilerplate, Groq API integration |
| **Day 2** | RAG pipeline (LangChain + FAISS + embeddings) | UI: upload page, clause display with risk color-coding |
| **Day 3** | Risk scoring engine + integration testing | UI: risk gauge chart, summary panel, Q&A chat interface |
| **Day 4** | Evaluation on sample contracts + README | Demo recording, final polish, documentation |

---

## Business Perspective

### Problem Statement

Legal documents are deliberately complex. The average employment contract is ~4,500 words; an NDA is ~2,000 words; a Fiverr Terms of Service runs over 10,000 words. Yet the consequences of not understanding them can be severe — lost intellectual property, unexpected non-compete clauses that prevent future employment, automatic subscriptions, or personal liability for company debts.

This is not a problem exclusive to the wealthy world. Pakistan's **freelancing economy generates over $1.5 billion annually**, yet Pakistani freelancers — the country's fastest-growing professional class — routinely sign client contracts from the US, UK, and EU without any legal support or understanding. The information asymmetry is extreme: international clients draft contracts with their lawyers; freelancers sign with their fingers crossed.

---

### Target Market

| Segment | Size | Pain Point |
|---------|------|-----------|
| **Pakistani freelancers** (primary) | 4M+ registered | Client contracts in English legal language they don't fully understand |
| **Global gig workers** (Fiverr/Upwork) | 73M+ in US alone | IP clauses, payment dispute terms, non-compete restrictions |
| **Fresh graduates / first-time employees** | Millions annually | Employment contracts, probation terms, IP assignment clauses |
| **Small businesses & startups** | 33M SMBs in the US | Vendor agreements, SaaS terms, partnership contracts |
| **Renters** | Universal | Lease agreements with auto-renewal and penalty clauses |

---

### Business Opportunity

The **global LegalTech market** is valued at **$30 billion (2023)** and projected to reach **$88 billion by 2030** (16.7% CAGR). AI-powered document review is the highest-growth subsegment within this space.

**Specific opportunity for freelancers:**
- Over 1.57 billion freelancers worldwide
- Pakistan is #4 globally in freelancer count, #3 in freelance earnings growth
- Zero affordable AI tools exist targeting this demographic in the MENA/South Asia region

This represents a **first-mover advantage** in an underserved but enormous market.

---

### Value Proposition

> **ClearClause gives every freelancer, employee, and small business the power to truly understand what they are signing — in plain English, in under 60 seconds, at a fraction of the cost of a lawyer.**

| Scenario | Without ClearClause | With ClearClause |
|----------|---------------------|-----------------|
| Reviewing a freelance contract | Sign blindly or pay $200+ for a lawyer | Upload → instant risk report in 60s |
| Understanding IP clause | Guess based on surface reading | Exact clause identified, explained in 2 sentences |
| Asking "can I work for competitors?" | Google your jurisdiction's law | Ask the chatbot — answers from your actual contract |
| Checking if contract is fair | No baseline for comparison | 0–100 risk score with explanations |

---

### Revenue Model

**Freemium SaaS (Web Platform):**

| Tier | Price | Features |
|------|-------|---------|
| **Free** | $0 | 3 documents/month, basic summary |
| **Pro** | $9.99/month | Unlimited documents, full risk analysis, Q&A, risk score |
| **Business** | $49/month | Team access, API, bulk processing, branded reports |
| **Enterprise** | Custom | White-label, CRM integrations, legal firm partnerships |

**Additional Revenue Streams:**
- **B2B API** — Integrate into Fiverr, Upwork, LinkedIn for in-platform contract review
- **Legal referral marketplace** — When risk is HIGH, connect users to vetted lawyers (10–15% referral fee)
- **White-label for HR platforms** — Companies embed ClearClause for employee onboarding

---

### Competitive Landscape

| Competitor | Limitation | Our Edge |
|------------|-----------|----------|
| Harvey AI | $40K+/year, enterprise-only | Consumer-accessible, affordable |
| LawGeex | Enterprise, not for individuals | Individual-first product |
| Kira Systems | Complex, M&A focus | Simple UX, any contract type |
| ChatGPT (general) | No legal domain specialization, hallucination risk | Purpose-built legal NLP, source-grounded answers |
| Manual reading | Time-consuming, unreliable | 60-second automated analysis |

**Unique Differentiator:** ClearClause is the only product combining legal-domain NLP (CUAD-trained), RAG-based document Q&A, and risk scoring in a single affordable interface — with specific attention to the South Asian freelancer market that is currently completely underserved.

---

### Social Impact

ClearClause is not just a commercial product — it is an **access-to-justice technology**. The failure to understand contracts disproportionately harms:

- Freelancers and gig workers who cannot afford legal advice
- First-generation professionals unfamiliar with corporate legal norms
- Immigrants signing contracts in a second language
- Residents of developing economies dealing with contracts from wealthier legal jurisdictions

By democratizing legal document comprehension, ClearClause acts as an equalizer — giving ordinary people the same informational advantage as corporations.

---

## Summary Table

| Aspect | Detail |
|--------|--------|
| **Project Name** | ClearClause |
| **Group** | Shehroz Ali (MSDSF25M012) · Arslan Ahmed (MSDSF25M001) |
| **Core NLP Tasks** | Extractive QA (clause detection) · Text Classification (risk) · Text Simplification · Abstractive Summarization · RAG-based Q&A |
| **Key Models** | DeBERTa-v3-CUAD · sentence-transformers · Groq LLaMA3 · FAISS |
| **Primary Dataset** | CUAD (13,500+ expert-annotated legal clauses, 41 categories) |
| **Prototype Deliverable** | Streamlit web app — upload contract → instant risk report + Q&A chatbot |
| **Development Timeline** | 4-day sprint (no from-scratch training required) |
| **Target Users** | Freelancers, gig workers, fresh employees, SMBs |
| **Primary Market** | Pakistan freelancer economy ($1.5B/yr) → Global gig economy (1.57B people) |
| **Business Model** | Freemium SaaS + B2B API + Legal referral marketplace |
| **Market Size** | $30B → $88B LegalTech market by 2030 |

---

*NLP Final Project Proposal — MS Data Science — April 2026*
