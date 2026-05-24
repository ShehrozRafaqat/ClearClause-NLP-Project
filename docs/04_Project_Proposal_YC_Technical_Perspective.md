# Project Deliverable 4: ClearClause - YC Strategic Proposal

**Business (Y Combinator) and Technical Perspective**  
**Program:** MPhil / MS Data Science  
**Course:** Natural Language Processing (NLP)  
**Submitted To:** Dr Adnan Abid  
**Submission Date:** May 2026

---

## Group Members

| S.No | Student ID | Name | Role |
|------|------------|------|------|
| 1 | MSDSF25M012 | Shehroz Ali | Founder - NLP pipeline, model integration, evaluation |
| 2 | MSDSF25M001 | Arslan Ahmed | Co-founder - system design, UI/demo, business analysis |

---

## 1. Project Name

**ClearClause**  
**AI-Powered Contract Risk Analyzer for Freelancers and Professionals**

---

## 2. One-Line YC Pitch

ClearClause helps freelancers, employees, and small businesses understand risky contracts in under 60 seconds by extracting legal clauses, scoring risk, rewriting legalese into plain English, and answering document-specific questions through grounded NLP.

---

## 3. Project Description

### 3.1 Problem

Freelancers, fresh graduates, small businesses, and independent professionals sign contracts every day without fully understanding the obligations hidden inside them. Employment agreements, NDAs, freelance service contracts, vendor agreements, leases, and platform terms often contain dense legal wording around intellectual property, termination, liability, payment, arbitration, non-compete restrictions, and automatic renewal.

The problem is not only legal complexity; it is information asymmetry. A company or client can draft a contract with legal support, while the signer often has no affordable way to identify what is risky before accepting it. Hiring a lawyer for every small freelance or employment contract is unrealistic, especially in emerging markets and early-career professional communities.

### 3.2 Solution

ClearClause is an NLP-powered contract review system that turns a legal document into a practical risk report. A user uploads a PDF, DOCX, or TXT contract, and the system:

1. Extracts contract text using document parsers.
2. Detects important legal clause types.
3. Classifies each clause as high, medium, or low risk.
4. Simplifies complex legal language into plain English.
5. Produces a structured document summary.
6. Builds a RAG index so the user can ask questions grounded in the uploaded contract.
7. Generates a 0-100 risk score and an exportable analysis report.

The output is not positioned as a replacement for a lawyer. It is an early-warning and comprehension layer that helps users know what to inspect, what to negotiate, and when to seek professional legal advice.

### 3.3 Target Users

| User Segment | Pain Point | ClearClause Benefit |
|--------------|------------|---------------------|
| Freelancers and gig workers | Client contracts contain IP transfer, payment, and liability risks | Fast plain-English risk scan before signing |
| Fresh graduates and employees | Employment terms are difficult to interpret | Highlights non-compete, probation, termination, and IP assignment clauses |
| Small businesses and startups | Vendor/SaaS agreements are reviewed without legal staff | Provides affordable first-pass contract intelligence |
| Renters and independent professionals | Lease and service agreements contain penalties and renewal traps | Converts hidden obligations into readable summaries |

---

## 4. Technical Perspective

### 4.1 Current System Architecture

```text
User Upload (PDF / DOCX / TXT)
        |
        v
Document Parser
pdfplumber / python-docx / text reader
        |
        v
Clause Extraction
Keyword NLP + optional DeBERTa-v3-CUAD legal QA model
        |
        v
Risk Scoring Engine
Clause taxonomy + weighted severity formula
        |
        +--------------------+
        |                    |
        v                    v
Plain-English AI        RAG Q&A Engine
Groq LLaMA3             sentence-transformers + FAISS + LangChain
        |                    |
        +---------+----------+
                  v
Streamlit Web App
Overview, clauses, summary, chat, charts, export report
```

### 4.2 Project Tech Stack

| Component | Technology | Reason for Selection |
|-----------|------------|----------------------|
| Document Parsing | `pdfplumber`, `python-docx`, TXT parser | Supports the most common contract formats while keeping ingestion local and lightweight. |
| Clause Extraction | Keyword NLP with optional `tomasonjo/deberta-v3-base-cuad` | Keyword extraction keeps the prototype fast and reliable; the CUAD-trained DeBERTa model provides a path toward legal-domain extractive QA. |
| Risk Classification | Rule-based legal clause taxonomy | Transparent for academic evaluation and explainable for users. Each clause category maps to high, medium, or low risk. |
| LLM Layer | Groq API with LLaMA3-8B | Fast and affordable inference for simplification, summarization, and grounded answers during demo scale. |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Efficient semantic embeddings for document chunks without heavy infrastructure. |
| Vector Store | FAISS | In-memory vector retrieval keeps private document context temporary and avoids database setup for the prototype. |
| RAG Framework | LangChain | Standard retrieval orchestration for contract-specific Q&A. |
| Frontend | Streamlit | Rapid Python-native UI for upload, charts, clause review, summaries, and chat. |
| Visualization | Plotly | Interactive risk gauge and chart breakdowns. |
| Configuration | `.env` + `python-dotenv` | Keeps API keys out of source code and supports simple local setup. |
| Future SaaS API | FastAPI, Docker, Azure | Clear path from academic prototype to scalable web/API product. |

### 4.3 Core NLP Modules

**Module 1 - Document Ingestion**

- Input: PDF, DOCX, or TXT contract.
- Process: extract raw text, normalize whitespace, split into paragraphs/chunks.
- Output: clean text corpus for extraction, summarization, and retrieval.

**Module 2 - Clause Extraction and Risk Detection**

- Current implementation: keyword-based detection across 14 legal clause categories.
- Upgrade path: extractive QA using a CUAD-trained DeBERTa-v3 model.
- Example high-risk clauses: unlimited liability, automatic renewal, unilateral termination, non-compete, indemnification, IP ownership/work-for-hire.
- Output: structured clause records with category, risk level, evidence text, and explanation.

**Module 3 - Plain-English Simplification**

- Technique: instruction prompting through Groq LLaMA3.
- Goal: rewrite legal language into one or two non-lawyer-friendly sentences without changing meaning.
- Business value: makes the product usable for non-specialists rather than only producing legal labels.

**Module 4 - RAG-Based Contract Q&A**

- Embedding model: `all-MiniLM-L6-v2`.
- Vector index: FAISS in memory.
- Framework: LangChain retrieval chain.
- User questions: "Can the client terminate me without reason?", "Who owns the work?", "Can I work with competitors?", "When do I get paid?"
- Guardrail: answers should be based only on retrieved contract chunks.

**Module 5 - Summarization**

- Produces a structured report covering obligations, rights, risks, money/payment terms, and important dates.
- Uses prompted LLM summarization over extracted contract content.

**Module 6 - Risk Scoring**

```text
Risk Score = (High clauses x 30 + Medium clauses x 15 + Low clauses x 5)
             normalized and capped at 100
```

Score bands:

| Score Range | Label | User Meaning |
|-------------|-------|--------------|
| 0-33 | Low Risk | Mostly standard; still review before signing. |
| 34-66 | Review Carefully | Several clauses deserve attention or negotiation. |
| 67-100 | High Risk | Strong warning; consider legal advice before signing. |

### 4.4 Evaluation Plan

| Module | Metric | Evaluation Method |
|--------|--------|-------------------|
| Clause Extraction | Precision, Recall, F1 | Compare detected clauses against manually labeled sample contracts or CUAD-style annotations. |
| Risk Classification | Accuracy, Macro-F1 | Evaluate severity labels against a human-created risk taxonomy. |
| Simplification | Flesch-Kincaid readability improvement, human rating | Compare original clause readability with simplified output. |
| Summarization | ROUGE-1/2/L and human usefulness rating | Compare generated summaries with reference summaries. |
| RAG Q&A | Answer faithfulness, source relevance, BERTScore | Check whether answers are grounded in retrieved contract chunks. |
| Product Performance | Latency, upload success rate | Measure time from upload to full report generation. |

---

## 5. Business Perspective - YC Application Fields

### 5.1 What Are You Making?

ClearClause is a legal-document comprehension product for people who cannot afford repeated legal review. The first version focuses on freelance, employment, NDA, vendor, and service contracts. The product converts a contract into a risk dashboard, plain-English explanations, and a contract-specific chatbot.

### 5.2 Founder Roles

- **Shehroz Ali - Founder:** Owns NLP pipeline design, clause extraction, risk scoring, model integration, and evaluation.
- **Arslan Ahmed - Co-founder:** Owns system design, Streamlit demo experience, report interface, business model, and go-to-market planning.

### 5.3 Category

**AI LegalTech / B2C-to-B2B SaaS**

ClearClause begins as a self-serve tool for freelancers and professionals, then expands into B2B APIs for freelance platforms, HR software, universities, startup incubators, and small-business service providers.

### 5.4 Domain Expertise

The team combines NLP implementation experience, RAG pipeline design, legal-domain transformer research, and a working prototype. The project is grounded in real contract-review workflows: clause extraction, risk explanation, summarization, and user Q&A.

The team also understands the Pakistan and South Asia freelancer market, where English contracts are common but legal support is expensive relative to contract value.

### 5.5 Why Now?

1. LLM APIs make legal-language simplification fast enough for consumer workflows.
2. Open legal NLP datasets such as CUAD reduce the need for expensive from-scratch labeling.
3. RAG makes document-grounded answers more reliable than generic chatbot responses.
4. Freelance and remote work continue to normalize cross-border contracts.
5. Enterprise legal AI tools are focused on law firms and large companies, leaving a large affordability gap.

### 5.6 Market Opportunity

External market research estimates the global legal AI market at approximately USD 1.45B in 2024, projected to approach USD 3.90B by 2030 with a 17.3 percent CAGR. Broader legal technology reports estimate a much larger legal tech market, with one report projecting USD 55B by 2029.

ClearClause does not need to win the enterprise legal market first. Its beachhead is the underserved contract-comprehension market for freelancers, students, early-career professionals, and small businesses. This segment is large, price-sensitive, and poorly served by enterprise-first legal AI platforms.

### 5.7 Competitors

| Competitor | Type | Limitation | ClearClause Edge |
|------------|------|------------|------------------|
| Harvey AI | Enterprise legal AI | Built for law firms and legal departments, not freelancers | Affordable, self-serve, contract-first workflow |
| LawGeex / Kira / contract review suites | Enterprise contract review | Procurement-heavy and designed for corporate legal teams | Lightweight upload-to-report experience |
| ChatGPT / generic LLMs | General AI assistant | Risk of hallucination and no fixed clause taxonomy | RAG-grounded answers plus explicit clause categories |
| Manual lawyer review | Professional service | High cost for small contracts | First-pass triage before paid legal help |
| Manual reading | No tool | Slow, inconsistent, and difficult for non-lawyers | 60-second risk report with plain-English explanations |

### 5.8 Revenue Process and Offering

**Freemium lead magnet**

- Free upload for a limited number of documents per month.
- Shows overall risk score, summary, and number of flagged clauses.
- Encourages upgrade for full clause-level explanations and chat.

**Paid subscriptions**

| Tier | Price | Offering |
|------|-------|----------|
| Free | USD 0 | Limited documents, basic summary, basic risk score |
| Pro | USD 9.99/month | Unlimited documents, full AI explanations, Q&A, export reports |
| Business | USD 49/month | Team workspace, bulk review, branded reports, priority usage |
| Enterprise/API | Custom | API access, HR/freelance platform integrations, admin controls |

**Additional revenue streams**

- Legal referral marketplace for high-risk contracts.
- B2B API for freelance platforms and HR onboarding tools.
- University and incubator licensing for student/founder contract review.

### 5.9 Go-To-Market Plan

1. Launch with Pakistan-based freelancer and student communities.
2. Publish contract teardown content showing real examples of risky clauses.
3. Partner with university entrepreneurship centers and freelancing bootcamps.
4. Offer free public demos for Fiverr/Upwork-style agreements and NDAs.
5. Convert frequent users to Pro and small agencies to Business.
6. Use anonymized clause-frequency analytics to improve product positioning.

### 5.10 Moat

- Domain-specific clause taxonomy for freelancer and employment contracts.
- Human feedback loop from user corrections and high-risk reports.
- Growing dataset of anonymized clause patterns by contract type.
- RAG-first architecture that keeps answers grounded in uploaded text.
- Regional positioning for South Asian freelancers before expanding globally.

### 5.11 Investment and Fundraising

The project is currently bootstrapped as an academic prototype. A YC-style pre-seed round would be used for:

- Legal expert review of clause taxonomy and disclaimers.
- Higher-quality annotated evaluation data.
- Secure document infrastructure and privacy controls.
- API and inference costs for early users.
- Product analytics, onboarding, and user acquisition experiments.
- B2B integrations with freelancer, HR, and small-business platforms.

### 5.12 Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| Users mistake the product for legal advice | Clear disclaimers, "not legal advice" positioning, referral flow for high-risk cases |
| LLM hallucination | RAG grounding, retrieved source snippets, conservative prompts, no answer when context is insufficient |
| Incorrect risk classification | Transparent rule taxonomy, human evaluation, legal expert review |
| Sensitive document privacy | Local parsing, temporary in-memory FAISS index, secure SaaS roadmap |
| Low willingness to pay | Freemium funnel, affordable pricing, B2B channels, legal referral revenue |

---

## 6. Project Deliverables and Launch Roadmap

### 6.1 Current Prototype Deliverables

- Streamlit app for upload and interactive analysis.
- PDF/DOCX/TXT document parser.
- Clause extraction module across 14 clause categories.
- Risk scoring and Plotly visualization.
- Groq-powered simplification and summarization.
- LangChain + FAISS RAG chatbot.
- Sample contracts and README setup instructions.
- Exportable analysis report.

### 6.2 Eight-Week Launch Roadmap

| Timeline | Milestone | Output |
|----------|-----------|--------|
| Week 2 | Evaluation Dataset MVP | 20-30 manually labeled contracts across freelance, NDA, employment, and service categories |
| Week 4 | Clause Intelligence Upgrade | CUAD-based DeBERTa QA option integrated and benchmarked against keyword baseline |
| Week 6 | Product Hardening | Better prompts, source snippets, privacy disclaimer, improved UI, exportable PDF report |
| Week 8 | Pilot Launch | Pilot with 25-50 freelancers/students, collect feedback, measure conversion and accuracy |

### 6.3 Academic Submission Artifacts

- Source code repository.
- Technical and YC-style business proposal.
- Working demo application.
- Evaluation plan and sample evaluation results.
- Final presentation/demo video.

---

## 7. Success Metrics

### 7.1 Technical Metrics

| Metric | Target |
|--------|--------|
| Clause extraction F1 | 0.80+ on project evaluation set |
| Risk label accuracy | 0.85+ on manually labeled clauses |
| Average report generation time | Under 60 seconds for standard contracts |
| RAG answer faithfulness | 0.85+ human-rated grounded answers |
| Simplification readability | At least 30 percent reduction in reading complexity |

### 7.2 Business Metrics

| Metric | Target |
|--------|--------|
| Activation | 60 percent of visitors upload or load a sample contract |
| Free-to-paid conversion | 5-8 percent in early freelancer segment |
| Retention | 30 percent monthly active return rate among Pro users |
| Referral trigger | 10 percent of high-risk reports create legal referral interest |
| B2B pilots | 3 pilot partners in universities, agencies, or freelancer communities |

---

## 8. Conclusion

ClearClause turns contract review from a confusing, expensive, and intimidating process into a fast NLP workflow that ordinary professionals can use before signing. Technically, the project demonstrates document parsing, legal clause extraction, risk classification, LLM simplification, summarization, RAG-based Q&A, and interactive visualization in a single application.

From a YC perspective, the product attacks a clear affordability gap: enterprise legal AI is advancing quickly, but freelancers and small teams still lack a practical tool for everyday contracts. By starting with a narrow, painful workflow and expanding toward platform integrations, ClearClause has a credible path from academic prototype to useful LegalTech SaaS.

---

## Sources Consulted

- GuardPoint AI - YC Strategic Proposal PDF supplied as the structural reference.
- Grand View Research, Legal AI Market Size and Outlook: https://www.grandviewresearch.com/horizon/outlook/legal-ai-market-size/global
- Grand View Research, Legal AI Market Report: https://www.grandviewresearch.com/industry-analysis/legal-ai-market-report
- Arizton, Legal Tech Market Report: https://www.arizton.com/market-reports/legal-tech-market
- Harvey AI official website: https://www.harvey.ai/
