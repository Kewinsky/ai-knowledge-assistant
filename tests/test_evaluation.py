import json
from pathlib import Path
from unittest.mock import Mock, call

import pytest

from knowledge_assistant import evaluation, generation
from knowledge_assistant.models import (
    DocumentChunk,
    EmbeddedChunk,
    EvaluationCase,
    SemanticSearchResult,
)


def create_chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            document_path=Path("documents/python.md"),
            index=0,
            content="Python is a programming language.",
        ),
        DocumentChunk(
            document_path=Path("documents/rag.md"),
            index=0,
            content="RAG retrieves relevant context.",
        ),
    ]


def test_load_evaluation_cases_preserves_order(tmp_path: Path) -> None:
    path = tmp_path / "questions.json"
    path.write_text(
        json.dumps(
            [
                {
                    "question": "  What is Python?  ",
                    "expected_source": "documents/python.md",
                },
                {
                    "question": "What is RAG?",
                    "expected_source": "documents/rag.md",
                },
            ]
        ),
        encoding="utf-8",
    )

    cases = evaluation.load_evaluation_cases(path)

    assert cases == [
        EvaluationCase(
            question="What is Python?",
            expected_source=Path("documents/python.md"),
        ),
        EvaluationCase(
            question="What is RAG?",
            expected_source=Path("documents/rag.md"),
        ),
    ]


def test_empty_evaluation_list_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "questions.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        evaluation.load_evaluation_cases(path)


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "questions.json"
    path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ValueError):
        evaluation.load_evaluation_cases(path)


@pytest.mark.parametrize(
    "data",
    [
        {},
        ["not an object"],
        [{"question": "Question without source"}],
        [{"question": 123, "expected_source": "documents/python.md"}],
        [{"question": "Question", "expected_source": 123}],
    ],
)
def test_invalid_evaluation_records_are_rejected(
    tmp_path: Path,
    data: object,
) -> None:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError):
        evaluation.load_evaluation_cases(path)


@pytest.mark.parametrize(
    "record",
    [
        {"question": "", "expected_source": "documents/python.md"},
        {"question": "   ", "expected_source": "documents/python.md"},
        {"question": "What is Python?", "expected_source": ""},
        {"question": "What is Python?", "expected_source": "   "},
    ],
)
def test_empty_question_or_source_is_rejected(
    tmp_path: Path,
    record: dict[str, str],
) -> None:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([record]), encoding="utf-8")

    with pytest.raises(ValueError):
        evaluation.load_evaluation_cases(path)


@pytest.mark.parametrize("limit", [0, -1])
def test_invalid_limit_is_rejected_before_embedding_calls(
    limit: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_embeddings_mock = Mock()
    create_embeddings_mock = Mock()
    monkeypatch.setattr(
        evaluation,
        "load_or_create_embeddings",
        load_embeddings_mock,
    )
    monkeypatch.setattr(
        evaluation,
        "create_embeddings",
        create_embeddings_mock,
    )

    with pytest.raises(ValueError):
        evaluation.evaluate_retrieval(
            Mock(),
            [EvaluationCase("What is Python?", Path("documents/python.md"))],
            create_chunks(),
            limit=limit,
        )

    load_embeddings_mock.assert_not_called()
    create_embeddings_mock.assert_not_called()


@pytest.mark.parametrize(
    ("cases", "chunks"),
    [
        ([], create_chunks()),
        (
            [EvaluationCase("What is Python?", Path("documents/python.md"))],
            [],
        ),
    ],
)
def test_empty_cases_or_chunks_are_rejected(
    cases: list[EvaluationCase],
    chunks: list[DocumentChunk],
) -> None:
    with pytest.raises(ValueError):
        evaluation.evaluate_retrieval(Mock(), cases, chunks)


def test_evaluate_retrieval_batches_questions_and_calculates_hit_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    chunks = create_chunks()
    embedded_chunks = [
        EmbeddedChunk(chunk=chunk, embedding=[float(index), 1.0])
        for index, chunk in enumerate(chunks)
    ]
    cases = [
        EvaluationCase("What is Python?", Path("documents/python.md")),
        EvaluationCase("What is chunking?", Path("documents/chunking.md")),
    ]
    python_result = SemanticSearchResult(chunk=chunks[0], score=0.9)
    rag_result = SemanticSearchResult(chunk=chunks[1], score=0.8)
    cache_path = Path("custom-cache/embeddings.json")
    load_embeddings_mock = Mock(return_value=embedded_chunks)
    create_embeddings_mock = Mock(return_value=[[1.0, 0.0], [0.0, 1.0]])
    semantic_search_mock = Mock(
        side_effect=[
            [python_result, python_result, rag_result],
            [rag_result],
        ]
    )
    generate_answer_mock = Mock()
    monkeypatch.setattr(
        evaluation,
        "load_or_create_embeddings",
        load_embeddings_mock,
    )
    monkeypatch.setattr(
        evaluation,
        "create_embeddings",
        create_embeddings_mock,
    )
    monkeypatch.setattr(
        evaluation,
        "semantic_search",
        semantic_search_mock,
    )
    monkeypatch.setattr(generation, "generate_answer", generate_answer_mock)

    summary = evaluation.evaluate_retrieval(
        client,
        cases,
        chunks,
        limit=3,
        cache_path=cache_path,
    )

    load_embeddings_mock.assert_called_once_with(client, chunks, cache_path)
    create_embeddings_mock.assert_called_once_with(
        client,
        ["What is Python?", "What is chunking?"],
    )
    assert semantic_search_mock.call_args_list == [
        call([1.0, 0.0], embedded_chunks, 3),
        call([0.0, 1.0], embedded_chunks, 3),
    ]
    assert [result.case for result in summary.results] == cases
    assert summary.results[0].retrieved_sources == [
        Path("documents/python.md"),
        Path("documents/rag.md"),
    ]
    assert [result.hit for result in summary.results] == [True, False]
    assert summary.hit_rate == 0.5
    generate_answer_mock.assert_not_called()


def test_custom_documents_directory_uses_canonical_source_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents_directory = tmp_path / "custom-documents"
    chunk = DocumentChunk(
        document_path=documents_directory / "python.md",
        index=0,
        content="Python is a programming language.",
    )
    embedded_chunks = [EmbeddedChunk(chunk=chunk, embedding=[1.0, 0.0])]
    search_result = SemanticSearchResult(chunk=chunk, score=0.9)
    monkeypatch.setattr(
        evaluation,
        "load_or_create_embeddings",
        Mock(return_value=embedded_chunks),
    )
    monkeypatch.setattr(
        evaluation,
        "create_embeddings",
        Mock(return_value=[[1.0, 0.0]]),
    )
    monkeypatch.setattr(
        evaluation,
        "semantic_search",
        Mock(return_value=[search_result]),
    )

    summary = evaluation.evaluate_retrieval(
        Mock(),
        [EvaluationCase("What is Python?", Path("documents/python.md"))],
        [chunk],
        documents_directory=documents_directory,
    )

    assert summary.results[0].retrieved_sources == [
        Path("documents/python.md")
    ]
    assert summary.results[0].hit is True
    assert summary.hit_rate == 1.0
