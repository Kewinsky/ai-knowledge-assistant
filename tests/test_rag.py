from pathlib import Path
from unittest.mock import Mock

import pytest

from knowledge_assistant import rag
from knowledge_assistant.models import (
    DocumentChunk,
    EmbeddedChunk,
    SemanticSearchResult,
)


def create_chunk() -> DocumentChunk:
    return DocumentChunk(
        document_path=Path("documents/python.md"),
        index=0,
        content="Python is a programming language.",
    )


@pytest.mark.parametrize(
    ("question", "chunks", "limit", "min_similarity_score"),
    [
        ("", [create_chunk()], 3, 0.5),
        ("   ", [create_chunk()], 3, 0.5),
        ("What is Python?", [], 3, 0.5),
        ("What is Python?", [create_chunk()], 0, 0.5),
        ("What is Python?", [create_chunk()], -1, 0.5),
        ("What is Python?", [create_chunk()], 3, -1.1),
        ("What is Python?", [create_chunk()], 3, 1.1),
    ],
)
def test_invalid_input_raises_before_api_calls(
    question: str,
    chunks: list[DocumentChunk],
    limit: int,
    min_similarity_score: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mocks = [Mock(), Mock(), Mock(), Mock()]
    monkeypatch.setattr(rag, "load_or_create_embeddings", mocks[0])
    monkeypatch.setattr(rag, "create_embeddings", mocks[1])
    monkeypatch.setattr(rag, "semantic_search", mocks[2])
    monkeypatch.setattr(rag, "generate_answer", mocks[3])

    with pytest.raises(ValueError):
        rag.answer_question(
            Mock(),
            question,
            chunks,
            limit,
            min_similarity_score,
        )

    for function_mock in mocks:
        function_mock.assert_not_called()


def test_success_uses_stripped_question_and_relevant_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    chunk = create_chunk()
    cache_path = Path("custom-cache/embeddings.json")
    embedded_chunks = [EmbeddedChunk(chunk=chunk, embedding=[1.0, 0.0])]
    relevant_result = SemanticSearchResult(chunk=chunk, score=0.8)
    irrelevant_result = SemanticSearchResult(chunk=chunk, score=0.4)
    load_embeddings_mock = Mock(return_value=embedded_chunks)
    create_embeddings_mock = Mock(return_value=[[1.0, 0.0]])
    semantic_search_mock = Mock(
        return_value=[relevant_result, irrelevant_result]
    )
    generate_answer_mock = Mock(return_value="Python is a programming language.")
    monkeypatch.setattr(rag, "load_or_create_embeddings", load_embeddings_mock)
    monkeypatch.setattr(rag, "create_embeddings", create_embeddings_mock)
    monkeypatch.setattr(rag, "semantic_search", semantic_search_mock)
    monkeypatch.setattr(rag, "generate_answer", generate_answer_mock)

    answer = rag.answer_question(
        client,
        "  What is Python?  ",
        [chunk],
        limit=3,
        min_similarity_score=0.7,
        cache_path=cache_path,
    )

    load_embeddings_mock.assert_called_once_with(client, [chunk], cache_path)
    create_embeddings_mock.assert_called_once_with(client, ["What is Python?"])
    semantic_search_mock.assert_called_once_with(
        [1.0, 0.0],
        embedded_chunks,
        3,
    )
    generate_answer_mock.assert_called_once_with(
        client,
        "What is Python?",
        [relevant_result],
    )
    assert answer.text == "Python is a programming language."
    assert answer.sources == [relevant_result]


def test_no_relevant_results_returns_fallback_without_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chunk = create_chunk()
    embedded_chunks = [EmbeddedChunk(chunk=chunk, embedding=[1.0, 0.0])]
    irrelevant_result = SemanticSearchResult(chunk=chunk, score=0.4)
    generate_answer_mock = Mock()
    monkeypatch.setattr(
        rag,
        "load_or_create_embeddings",
        Mock(return_value=embedded_chunks),
    )
    monkeypatch.setattr(
        rag,
        "create_embeddings",
        Mock(return_value=[[1.0, 0.0]]),
    )
    monkeypatch.setattr(
        rag,
        "semantic_search",
        Mock(return_value=[irrelevant_result]),
    )
    monkeypatch.setattr(rag, "generate_answer", generate_answer_mock)

    answer = rag.answer_question(Mock(), "Unknown question", [chunk])

    assert answer.text == rag.INSUFFICIENT_CONTEXT_ANSWER
    assert answer.sources == []
    generate_answer_mock.assert_not_called()
