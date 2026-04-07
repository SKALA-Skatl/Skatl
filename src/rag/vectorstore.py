from __future__ import annotations

"""Vector index builder and loader."""

import json
import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from .collections import COLLECTIONS, get_allowed_sources
from .config import RAGConfig


def build_and_save_indices(
    documents: list[Document],
    config: RAGConfig,
    project_root: Path,
    collection_names: list[str] | None = None,
) -> dict[str, dict[str, int]]:
    """Build one shared FAISS index and summarize profile coverage."""

    embeddings = _build_embeddings(config)
    index_root = config.resolved_index_dir(project_root)
    index_root.mkdir(parents=True, exist_ok=True)

    selected_names = collection_names or [collection.name for collection in COLLECTIONS]
    summary: dict[str, dict[str, int]] = {}
    vectorstore = _build_and_save_single_index(
        documents=documents,
        embeddings=embeddings,
        index_dir=config.resolved_shared_index_dir(project_root),
    )

    for collection_name in selected_names:
        allowed_sources = get_allowed_sources(collection_name)
        document_count = sum(
            1 for document in documents
            if document.metadata.get("source") in allowed_sources
        )
        summary[collection_name] = {
            "documents": document_count,
            "vectors": document_count,
        }

    summary["shared_index"] = {
        "documents": len(documents),
        "vectors": vectorstore.index.ntotal,
    }

    manifest_path = index_root / "manifest.json"
    manifest_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def load_index(config: RAGConfig, project_root: Path, collection_name: str | None = None) -> FAISS:
    """Load the shared FAISS index."""

    index_dir = config.resolved_shared_index_dir(project_root)
    return FAISS.load_local(
        str(index_dir),
        _build_embeddings(config),
        allow_dangerous_deserialization=True,
    )


def similarity_search(
    *,
    collection_name: str,
    question: str,
    config: RAGConfig,
    project_root: Path,
    k: int | None = None,
) -> list[Document]:
    """Run a collection-filtered similarity search on the shared index."""

    vectorstore = load_index(config, project_root, collection_name)
    results = vectorstore.similarity_search(question, k=max((k or config.search_k) * 8, 20))
    allowed_sources = get_allowed_sources(collection_name)
    filtered = [
        document for document in results
        if document.metadata.get("source") in allowed_sources
    ]
    return filtered[: k or config.search_k]


def _build_and_save_single_index(
    *,
    documents: list[Document],
    embeddings: HuggingFaceEmbeddings,
    index_dir: Path,
) -> FAISS:
    """Create and persist a single FAISS index."""

    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(index_dir))
    return vectorstore


def _build_embeddings(config: RAGConfig) -> HuggingFaceEmbeddings:
    """Create the embedding model wrapper."""

    # 기본은 Hugging Face 모델명을 사용하고, 캐시 경로가 있으면 재사용합니다.
    device = config.device or _detect_device()
    cache_dir = _resolve_cache_dir(config)
    return HuggingFaceEmbeddings(
        model_name=config.embedding_model,
        cache_folder=str(cache_dir) if cache_dir else None,
        model_kwargs={"device": device},
        show_progress=False,
        encode_kwargs={"normalize_embeddings": True},
    )


def _detect_device() -> str:
    """Pick the best available torch device."""

    try:
        import torch
    except ImportError:
        return "cpu"

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _resolve_cache_dir(config: RAGConfig) -> Path | None:
    """Resolve the Hugging Face cache directory."""

    if config.model_cache_dir:
        return config.model_cache_dir

    for env_name in ("HF_HOME", "TRANSFORMERS_CACHE", "HUGGINGFACE_HUB_CACHE"):
        value = os.getenv(env_name)
        if value:
            return Path(value)
    return None
