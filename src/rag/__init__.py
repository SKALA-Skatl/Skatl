"""RAG utilities for document ingestion, indexing, and retrieval."""

from .collections import COLLECTIONS, filter_documents_for_collection, get_allowed_sources, get_collection, get_collection_names
from .config import RAGConfig, SHARED_INDEX_DIRNAME
from .pdf_ingest import build_documents_from_path, build_documents_from_paths

__all__ = [
    "COLLECTIONS",
    "RAGConfig",
    "SHARED_INDEX_DIRNAME",
    "build_documents_from_path",
    "build_documents_from_paths",
    "filter_documents_for_collection",
    "get_allowed_sources",
    "get_collection",
    "get_collection_names",
]
