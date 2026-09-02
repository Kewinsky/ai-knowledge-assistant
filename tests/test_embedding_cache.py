from pathlib import Path
from unittest.mock import Mock

import pytest

from knowledge_assistant import embedding_cache
from knowledge_assistant.embeddings import EMBEDDING_DIMENSIONS
from knowledge_assistant.models import DocumentChunk, EmbeddedChunk


def create_chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            document_path=Path("documents/python.md"),
            index=0,
            content="Python is a programming language.",
        ),
        DocumentChunk(
            document_path=Path("documents/rag.md"),
            index=1,
            content="RAG retrieves relevant context.",
        ),
    ]


def create_embedded_chunks(
    chunks: list[DocumentChunk],
) -> list[EmbeddedChunk]:
    return [
        EmbeddedChunk(
            chunk=chunk,
            embedding=[float(index + 1)] * EMBEDDING_DIMENSIONS,
        )
        for index, chunk in enumerate(chunks)
    ]


def test_cache_miss_creates_embeddings_and_cache_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunks = create_chunks()
    expected = create_embedded_chunks(chunks)
    embed_chunks_mock = Mock(return_value=expected)
    monkeypatch.setattr(embedding_cache, "embed_chunks", embed_chunks_mock)
    cache_path = tmp_path / "embeddings.json"

    result = embedding_cache.load_or_create_embeddings(
        Mock(),
        chunks,
        cache_path,
    )

    assert result == expected
    assert cache_path.exists()
    embed_chunks_mock.assert_called_once()


def test_cache_hit_does_not_create_embeddings_again(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunks = create_chunks()
    expected = create_embedded_chunks(chunks)
    embed_chunks_mock = Mock(return_value=expected)
    monkeypatch.setattr(embedding_cache, "embed_chunks", embed_chunks_mock)
    cache_path = tmp_path / "embeddings.json"

    embedding_cache.load_or_create_embeddings(Mock(), chunks, cache_path)
    result = embedding_cache.load_or_create_embeddings(Mock(), chunks, cache_path)

    assert result == expected
    embed_chunks_mock.assert_called_once()


def test_changed_chunk_content_invalidates_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunks = create_chunks()
    changed_chunks = [
        DocumentChunk(
            document_path=chunk.document_path,
            index=chunk.index,
            content=f"{chunk.content} Changed.",
        )
        for chunk in chunks
    ]
    embed_chunks_mock = Mock(
        side_effect=[
            create_embedded_chunks(chunks),
            create_embedded_chunks(changed_chunks),
        ]
    )
    monkeypatch.setattr(embedding_cache, "embed_chunks", embed_chunks_mock)
    cache_path = tmp_path / "embeddings.json"

    embedding_cache.load_or_create_embeddings(Mock(), chunks, cache_path)
    result = embedding_cache.load_or_create_embeddings(
        Mock(),
        changed_chunks,
        cache_path,
    )

    assert [item.chunk for item in result] == changed_chunks
    assert embed_chunks_mock.call_count == 2


def test_invalid_json_regenerates_embeddings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunks = create_chunks()
    expected = create_embedded_chunks(chunks)
    embed_chunks_mock = Mock(return_value=expected)
    monkeypatch.setattr(embedding_cache, "embed_chunks", embed_chunks_mock)
    cache_path = tmp_path / "embeddings.json"

    embedding_cache.load_or_create_embeddings(Mock(), chunks, cache_path)
    cache_path.write_text("{invalid json", encoding="utf-8")
    result = embedding_cache.load_or_create_embeddings(Mock(), chunks, cache_path)

    assert result == expected
    assert embed_chunks_mock.call_count == 2


def test_cached_embeddings_preserve_chunk_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunks = create_chunks()
    expected = create_embedded_chunks(chunks)
    embed_chunks_mock = Mock(return_value=expected)
    monkeypatch.setattr(embedding_cache, "embed_chunks", embed_chunks_mock)
    cache_path = tmp_path / "embeddings.json"

    embedding_cache.load_or_create_embeddings(Mock(), chunks, cache_path)
    result = embedding_cache.load_or_create_embeddings(Mock(), chunks, cache_path)

    assert [item.chunk for item in result] == chunks
    assert [item.embedding[0] for item in result] == [1.0, 2.0]

