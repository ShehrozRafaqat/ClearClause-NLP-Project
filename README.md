<p align="center">
  <img src="https://img.shields.io/badge/NLP-Legal%20AI-2563EB?style=for-the-badge&logo=openai&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
</p>

<h1 align="center">⚖️ ClearClause</h1>
<p align="center"><strong>AI-Powered Contract Risk Analyzer for Freelancers & Professionals</strong></p>
<p align="center">
  NLP Final Project · MS Data Science<br>
  <b>Shehroz Ali</b> (MSDSF25M012) &nbsp;·&nbsp; <b>Arslan Ahmed</b> (MSDSF25M001)
</p>

---

## 🎯 What is ClearClause?

ClearClause is an end-to-end NLP system that transforms complex legal contracts into clear, actionable intelligence — in under 60 seconds.

Upload a PDF or Word contract and ClearClause will:

| Feature | Description |
|---------|-------------|
| 🔍 **Clause Extraction** | Identifies 14 legal clause types using keyword NLP + optional DeBERTa-v3-CUAD |
| ⚠️ **Risk Classification** | Labels each clause HIGH / MEDIUM / LOW risk with explanations |
| 💬 **Plain-English Simplification** | Converts legal jargon to readable sentences via Groq LLaMA3 |
| 📋 **Document Summarization** | Generates a structured 4-section summary (obligations, rights, risks, finances) |
| 🤖 **RAG Q&A Chatbot** | Answers questions about your specific contract using LangChain + FAISS |
| 📊 **Risk Score Gauge** | 0–100 animated Plotly gauge with breakdown donut chart |
| ⬇️ **Export Report** | Downloadable full HTML analysis report |

---

## 🏗️ System Architecture

```
Upload (PDF/DOCX/TXT)
        │
        ▼
┌─────────────────────┐
│  Document Parser    │  pdfplumber / python-docx
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Clause Extractor   │  Keyword NLP (14 types) + DeBERTa-v3-CUAD (optional)
└────┬───────────┬────┘
     │           │
     ▼           ▼
┌─────────┐  ┌──────────────┐
│  Risk   │  │  AI Engine   │  Groq LLaMA3-8b – Simplification + Summary
│  Scorer │  └──────┬───────┘
└────┬────┘         │
     │              ▼
     │     ┌────────────────┐
     │     │  RAG Engine    │  LangChain + FAISS + sentence-transformers
     │     └───────┬────────┘
     └─────────────┼──────────────────┐
                   ▼                  ▼
         ┌──────────────────────────────────┐
         │      Streamlit Web App           │
         │  Overview · Clauses · Chat · PDF │
         └──────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/ShehrozRafaqat/ClearClause-NLP-Project.git
cd ClearClause-NLP-Project
```

### 2. Create a virtual environment & install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Get a free Groq API key

Sign up at [console.groq.com](https://console.groq.com) (takes 30 seconds, completely free).

### 4. Configure

```bash
cp .env.example .env
# Edit .env and add your key:
# GROQ_API_KEY=your_key_here
```

### 5. Run

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

> **No API key?** You can still click **"Load Demo Contract"** and the keyword-based clause extraction (no AI) will run instantly.

---

## 📦 Project Structure

```
ClearClause-NLP-Project/
├── app.py                  ← Main Streamlit application
├── config.py               ← 14 clause definitions, risk mappings, demo contract
├── requirements.txt        ← All Python dependencies
├── .env.example            ← Environment variable template
│
├── src/
│   ├── parser.py           ← Document ingestion (PDF/DOCX/TXT)
│   ├── extractor.py        ← NLP clause extraction (keyword + CUAD model)
│   ├── scorer.py           ← Risk scoring + Plotly gauge
│   ├── ai_engine.py        ← Groq LLM: simplification + summarization
│   └── rag_engine.py       ← LangChain RAG: FAISS + embeddings + Q&A
│
├── assets/
│   └── style.css           ← Custom dark theme CSS
│
└── ClearClause_NLP_Proposal.pdf   ← Full project proposal
```

---

## 🧠 NLP Components

### Clause Types Detected (14 categories)

| Risk | Clause Type |
|------|------------|
| 🔴 HIGH | IP Ownership/Work-for-Hire, Automatic Renewal, Unilateral Termination, Unlimited Liability, Non-Compete, Indemnification |
| 🟡 MEDIUM | Non-Solicitation, Governing Law, Arbitration, Limitation of Liability, Confidentiality/NDA, Change of Control |
| 🟢 LOW | Payment Terms, Effective Date & Term |

### Models & Tools

| Component | Technology |
|-----------|-----------|
| Clause Extraction | Keyword NLP (fast, always-on) + `tomasonjo/deberta-v3-base-cuad` (optional) |
| Text Simplification | Groq API — LLaMA3-8b-8192 |
| Document Summary | Groq API — LLaMA3-8b-8192 |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector Store | FAISS (in-memory) |
| RAG Framework | LangChain |
| UI | Streamlit |
| Charts | Plotly |

### Evaluation Metrics

| Module | Metric |
|--------|--------|
| Clause Extraction | F1-Score, Precision, Recall |
| Risk Classification | Accuracy, Macro-F1 |
| Summarization | ROUGE-1/2/L |
| Simplification | Flesch-Kincaid readability improvement |
| Q&A Faithfulness | BERTScore |

---

## 💼 Business Context

Pakistan is **#4 globally in freelancers**, generating **$1.5B+/year** — yet no affordable legal AI tool exists for this market. ClearClause targets the **$30B → $88B LegalTech market** (CAGR 16.7%) with a freemium SaaS model:

- **Free**: 3 docs/month
- **Pro**: $9.99/month — unlimited + full AI
- **Business**: $49/month — team + API

---

## 📄 Proposal

The full project proposal PDF is included at the root: `ClearClause_NLP_Proposal.pdf`

---

## 🔐 Privacy

Your documents never leave your machine. All vector embeddings are built in-memory using FAISS and are discarded when the session ends.

---

<p align="center">Made with ❤️ for NLP Final Project · MS Data Science · April 2026</p>
