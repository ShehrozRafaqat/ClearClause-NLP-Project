"""Optional Groq integration.

The project is fully demoable offline. When a Groq API key is provided, these
helpers replace deterministic text with LLM-polished explanations and answers.
"""

from __future__ import annotations

import os

from .models import ClauseFinding


DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


class GroqAssistant:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _load_client(self):
        if self._client is None:
            from groq import Groq

            self._client = Groq(api_key=self.api_key)
        return self._client

    def complete(self, system: str, user: str, max_tokens: int = 450, temperature: float = 0.1) -> str:
        if not self.available:
            raise ValueError("Groq API key is not configured.")
        client = self._load_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()

    def simplify_clause(self, finding: ClauseFinding) -> str:
        system = (
            "You simplify contract clauses for non-lawyers. Be accurate, plain, and concise. "
            "Do not give external legal advice. Return 2 short sentences plus one action sentence."
        )
        user = (
            f"Clause type: {finding.title}\n"
            f"Risk level: {finding.severity}\n"
            f"Contract text: {finding.snippet}\n"
            f"Existing recommendation: {finding.recommendation}"
        )
        return self.complete(system, user, max_tokens=180)

    def summarize(self, contract_text: str, detected_titles: list[str]) -> str:
        system = (
            "You are ClearClause, a contract analyst for freelancers. Summarize only facts from the document. "
            "Use markdown headings: Executive Snapshot, Main Risks, Payment and Deadlines, Before Signing."
        )
        user = (
            "Detected clause types: "
            + ", ".join(detected_titles[:14])
            + "\n\nContract text:\n"
            + contract_text[:18000]
        )
        return self.complete(system, user, max_tokens=650)

    def answer(self, question: str, context: str) -> str:
        system = (
            "Answer using only the contract excerpts supplied. If the answer is not supported, say you cannot find it. "
            "Use plain English and cite the relevant excerpt briefly."
        )
        user = f"Question: {question}\n\nContract excerpts:\n{context[:6000]}"
        return self.complete(system, user, max_tokens=360, temperature=0.0)

