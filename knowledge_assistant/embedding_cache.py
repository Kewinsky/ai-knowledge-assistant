import hashlib
import json
import math
from pathlib import Path

from openai import OpenAI

from knowledge_assistant.embeddings import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    embed_chunks,
)
from knowledge_assistant.models import DocumentChunk, EmbeddedChunk


def _create_fingerprint(chunks: list[DocumentChunk]) -> str:
    fingerprint_data = [
        EMBEDDING_MODEL,
        EMBEDDING_DIMENSIONS,
        [
            [str(chunk.document_path), chunk.index, chunk.content]
            for chunk in chunks
        ],
    ]
    serialized_data = json.dumps(
        fingerprint_data,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized_data.encode("utf-8")).hexdigest()


def _load_cached_embeddings(
    cache_path: Path,
    fingerprint: str,
    chunk_count: int,
) -> list[list[float]] | None:
    try:
        with cache_path.open(encoding="utf-8") as cache_file:
            cache_data: object = json.load(cache_file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not isinstance(cache_data, dict):
        return None

    if cache_data.get("model") != EMBEDDING_MODEL:
        return None

    if cache_data.get("dimensions") != EMBEDDING_DIMENSIONS:
        return None

    if cache_data.get("fingerprint") != fingerprint:
        return None

    cached_embeddings = cache_data.get("embeddings")

    if not isinstance(cached_embeddings, list):
        return None

    if len(cached_embeddings) != chunk_count:
        return None

    embeddings: list[list[float]] = []
    for cached_embedding in cached_embeddings:
        if (
            not isinstance(cached_embedding, list)
            or len(cached_embedding) != EMBEDDING_DIMENSIONS
        ):
            return None

        embedding: list[float] = []

        for value in cached_embedding:
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                return None

            embedding.append(float(value))

        embeddings.append(embedding)

    return embeddings


def _save_embeddings(
    cache_path: Path,
    fingerprint: str,
    embedded_chunks: list[EmbeddedChunk],
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_data = {
        "model": EMBEDDING_MODEL,
        "dimensions": EMBEDDING_DIMENSIONS,
        "fingerprint": fingerprint,
        "embeddings": [item.embedding for item in embedded_chunks],
    }

    with cache_path.open("w", encoding="utf-8") as cache_file:
        json.dump(cache_data, cache_file)


def load_or_create_embeddings(
    client: OpenAI,
    chunks: list[DocumentChunk],
    cache_path: Path = Path(".cache/embeddings.json"),
) -> list[EmbeddedChunk]:
    fingerprint = _create_fingerprint(chunks)
    cached_embeddings = _load_cached_embeddings(
        cache_path,
        fingerprint,
        len(chunks),
    )

    # Return cached embeddings if available
    if cached_embeddings is not None:
        return [
            EmbeddedChunk(chunk=chunk, embedding=embedding)
            for chunk, embedding in zip(chunks, cached_embeddings, strict=True)
        ]

    # Create new embeddings and save to cache
    embedded_chunks = embed_chunks(client, chunks)
    _save_embeddings(cache_path, fingerprint, embedded_chunks)
    return embedded_chunks
