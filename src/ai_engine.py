"""
Module 4 – AI Engine (LangChain + Groq)
Handles clause simplification and full-document summarization.
"""
from __future__ import annotations
import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.extractor import DetectedClause
from config import GROQ_MODEL


class AIEngine:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.getenv("GROQ_API_KEY", "")
        if not key:
            raise ValueError("GROQ_API_KEY is required.")

        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=key,
            model_name=GROQ_MODEL,
            max_tokens=512,
        )

        # ── Simplification prompt ──────────────────────────────────────────
        self._simp_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a legal plain-language translator. "
             "Rewrite the clause in 1-3 simple sentences a non-lawyer understands. "
             "Be accurate. No filler phrases. Return only the simplified text."),
            ("user", "Clause type: {clause_type}\n\nText:\n{text}"),
        ])

        # ── Summarisation prompt ───────────────────────────────────────────
        self._summ_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert contract analyst. "
             "Summarise the contract below. "
             "Use exactly this markdown structure:\n\n"
             "### 📌 Key Obligations\n- ...\n\n"
             "### ✅ Rights Granted\n- ...\n\n"
             "### ⚠️ Key Risks\n- ...\n\n"
             "### 💰 Finances & Important Dates\n- ...\n\n"
             "Keep the whole summary under 350 words. Only use facts from the contract."),
            ("user", "Contract:\n\n{text}"),
        ])

        parser = StrOutputParser()
        self._simp_chain  = self._simp_prompt  | self.llm | parser
        self._summ_chain  = self._summ_prompt  | self.llm | parser

    # ── Public API ─────────────────────────────────────────────────────────
    def simplify_clause(self, clause: DetectedClause) -> str:
        try:
            return self._simp_chain.invoke({
                "clause_type": clause.clause_type,
                "text": clause.snippet[:1500],
            })
        except Exception as e:
            return f"*(simplification unavailable: {e})*"

    def summarize_document(self, text: str) -> str:
        try:
            return self._summ_chain.invoke({"text": text[:20000]})
        except Exception as e:
            return f"*(summary unavailable: {e})*"
