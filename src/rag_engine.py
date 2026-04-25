"""
Module 5 – RAG Engine  (compatible with langchain>=1.2 + langchain-community>=0.4)
Conversational Q&A grounded exclusively in the uploaded contract text.
"""
from __future__ import annotations
import os

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from config import GROQ_MODEL


_SYSTEM = """You are ClearClause, a friendly legal assistant.
Answer the user's question using ONLY the following contract text.
If the answer is not in the text, say: "I can't find this in your contract."
Be concise and use plain English. Never give general legal advice outside the document."""

_PROMPT = ChatPromptTemplate.from_template(
    _SYSTEM + "\n\nContract excerpt:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)


def _format_docs(docs) -> str:
    return "\n\n---\n\n".join(d.page_content for d in docs)


class RAGEngine:
    def __init__(self, document_text: str, api_key: str | None = None):
        key = api_key or os.getenv("GROQ_API_KEY", "")
        if not key:
            raise ValueError("GROQ_API_KEY is not set.")

        self.text = document_text
        self._built  = False

        self.llm = ChatGroq(
            temperature=0.0,
            groq_api_key=key,
            model_name=GROQ_MODEL,
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self.chain = None

    def build_index(self):
        """Chunk the document and build the in-memory FAISS vector index."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800, chunk_overlap=150
        )
        texts = splitter.split_text(self.text) or ["(empty document)"]

        vs = FAISS.from_texts(texts, self.embeddings)
        retriever = vs.as_retriever(search_kwargs={"k": 4})

        self.chain = (
            {"context": retriever | _format_docs, "question": RunnablePassthrough()}
            | _PROMPT
            | self.llm
            | StrOutputParser()
        )
        self._built = True

    def query(self, question: str) -> str:
        if not self._built:
            self.build_index()
        try:
            return self.chain.invoke(question)
        except Exception as e:
            return f"⚠️ Error: {e}"
