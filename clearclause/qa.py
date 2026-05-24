"""Retrieval based Q&A for uploaded contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import ClauseFinding


@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[str]
    confidence: float


class ContractQA:
    def __init__(self, document_text: str, findings: list[ClauseFinding]):
        self.document_text = document_text
        self.findings = findings
        self.chunks = _chunk_text(document_text)
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        self.matrix = self.vectorizer.fit_transform(self.chunks or ["empty document"])

    def answer(self, question: str) -> Answer:
        question = question.strip()
        if not question:
            return Answer("Ask a specific question about the contract.", [], 0.0)

        finding = self._matching_finding(question)
        source_chunks = self.retrieve(question, top_k=3)
        sources = [chunk for chunk, _ in source_chunks]

        if finding:
            answer = (
                f"{finding.plain_english}\n\n"
                f"Negotiation note: {finding.recommendation}\n\n"
                f"Evidence: {finding.snippet}"
            )
            return Answer(answer, [finding.snippet, *sources[:2]], max(0.72, finding.confidence))

        if not source_chunks or source_chunks[0][1] < 0.05:
            return Answer(
                "I could not find a clear answer in the contract text. Try asking about payment, IP ownership, termination, liability, confidentiality, or dispute resolution.",
                [],
                0.12,
            )

        best_chunk, score = source_chunks[0]
        answer = (
            "Based on the most relevant contract text, this is the strongest evidence I found:\n\n"
            f"{best_chunk}\n\n"
            "Because the offline Q&A mode is extractive, treat this as sourced evidence rather than legal advice."
        )
        return Answer(answer, sources, min(0.88, max(0.35, score * 2.4)))

    def retrieve(self, question: str, top_k: int = 4) -> list[tuple[str, float]]:
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.matrix).ravel()
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        return [(self.chunks[idx], float(score)) for idx, score in ranked[:top_k] if score > 0]

    def _matching_finding(self, question: str) -> ClauseFinding | None:
        q = question.lower()
        intents = {
            "ip_ownership": [
                "own", "ownership", "intellectual property", "source code", "portfolio",
                "work product", "deliverable", "copyright", "assign", "license to use",
            ],
            "payment_terms": [
                "payment", "paid", "invoice", "money", "fee", "rate", "net ",
                "deposit", "milestone", "compensation", "withhold",
            ],
            "unilateral_termination": [
                "terminate", "fire", "cancel", "end contract", "without cause",
                "for convenience", "notice", "kill fee",
            ],
            "non_compete": [
                "compete", "competitor", "other clients", "similar clients",
                "future work", "non-compete", "restricted",
            ],
            "automatic_renewal": [
                "renew", "renewal", "cancel deadline", "non-renewal", "auto-renew",
                "extend", "successive",
            ],
            "unlimited_liability": [
                "liability", "damages", "cap", "financial risk", "lost profits",
                "indirect", "consequential", "exposure",
            ],
            "indemnification": [
                "indemnify", "legal fees", "hold harmless", "claim", "defend",
                "attorneys' fees", "third party",
            ],
            "confidentiality": [
                "confidential", "nda", "secret", "disclose", "portfolio",
                "trade secret", "proprietary",
            ],
            "arbitration": [
                "arbitration", "court", "sue", "dispute", "jury", "class action",
                "small claims",
            ],
            "governing_law": [
                "governing law", "jurisdiction", "venue", "country", "what law",
                "which law", "which court",
            ],
            "non_solicitation": [
                "solicit", "employees", "customers", "hire", "poach", "recruit",
            ],
            "exclusivity": [
                "exclusive", "only client", "other clients", "exclusivity",
            ],
            "data_privacy": [
                "data", "privacy", "gdpr", "personal data", "security breach",
                "incident", "encryption",
            ],
            "scope_acceptance": [
                "scope", "deliverable", "acceptance", "revision", "change request",
                "what do i deliver",
            ],
            "liability_cap": [
                "liability cap", "limit of liability", "limitation of liability",
                "maximum liability", "not liable",
            ],
            "assignment_change": [
                "assign", "assignment", "transfer", "change of control",
                "merger", "acquisition",
            ],
            "term_effective_date": [
                "effective date", "start date", "term of", "expire", "begins",
                "how long",
            ],
        }
        for clause_id, keywords in intents.items():
            if any(keyword in q for keyword in keywords):
                match = next((finding for finding in self.findings if finding.clause_id == clause_id), None)
                if match:
                    return match
        return None


def _chunk_text(text: str, chunk_size: int = 950, overlap: int = 150) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        normalized = re.sub(r"\s+", " ", paragraph)
        if len(current) + len(normalized) + 2 <= chunk_size:
            current = f"{current}\n\n{normalized}".strip()
        else:
            if current:
                chunks.append(current)
            if len(normalized) > chunk_size:
                start = 0
                while start < len(normalized):
                    chunks.append(normalized[start : start + chunk_size])
                    start += max(1, chunk_size - overlap)
                current = ""
            else:
                current = normalized
    if current:
        chunks.append(current)
    return chunks or [text[:chunk_size]]

