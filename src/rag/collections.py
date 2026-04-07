from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document


@dataclass(frozen=True, slots=True)
class RAGCollection:
    name: str
    description: str
    sources: tuple[str, ...]


COLLECTIONS: tuple[RAGCollection, ...] = (
    RAGCollection(
        name="market_agent",
        description="Market research only. Used by the market agent.",
        sources=("market_report.pdf", "analyst_report.pdf"),
    ),
    RAGCollection(
        name="skon_agent",
        description="SK On analysis with company facts plus market context.",
        sources=("skon.pdf", "market_report.pdf", "analyst_report.pdf"),
    ),
    RAGCollection(
        name="catl_agent",
        description="CATL analysis with company facts plus market context.",
        sources=("catl.pdf", "market_report.pdf", "analyst_report.pdf"),
    ),
)


def get_collection(name: str) -> RAGCollection:
    for collection in COLLECTIONS:
        if collection.name == name:
            return collection
    raise KeyError(f"Unknown collection: {name}")


def get_collection_names() -> list[str]:
    return [collection.name for collection in COLLECTIONS]


def get_allowed_sources(name: str) -> set[str]:
    return set(get_collection(name).sources)


def filter_documents_for_collection(documents: list[Document], collection: RAGCollection) -> list[Document]:
    allowed_sources = set(collection.sources)
    return [document for document in documents if document.metadata.get("source") in allowed_sources]
