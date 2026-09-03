import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from openai import OpenAI

from knowledge_assistant import evaluation
from knowledge_assistant.documents import load_markdown_files, split_documents
from knowledge_assistant.models import DocumentChunk, EmbeddedChunk


DOCUMENTS_DIRECTORY = Path("documents")
QUESTIONS_PATH = Path("evaluation/questions.json")
GOLDEN_VECTORS_PATH = Path("evaluation/golden_vectors.json")


def load_golden_vectors() -> tuple[
    dict[str, list[float]],
    dict[str, list[float]],
]:
    data: object = json.loads(GOLDEN_VECTORS_PATH.read_text(encoding="utf-8"))

    assert isinstance(data, dict)
    document_vectors = data.get("documents")
    question_vectors = data.get("questions")
    assert isinstance(document_vectors, dict)
    assert isinstance(question_vectors, dict)

    vectors: list[list[float]] = []
    parsed_document_vectors: dict[str, list[float]] = {}
    parsed_question_vectors: dict[str, list[float]] = {}

    for key, value in document_vectors.items():
        assert isinstance(key, str)
        assert isinstance(value, list)
        assert all(isinstance(item, float) for item in value)
        parsed_document_vectors[key] = value
        vectors.append(value)

    for key, value in question_vectors.items():
        assert isinstance(key, str)
        assert isinstance(value, list)
        assert all(isinstance(item, float) for item in value)
        parsed_question_vectors[key] = value
        vectors.append(value)

    assert vectors
    assert len({len(vector) for vector in vectors}) == 1
    return parsed_document_vectors, parsed_question_vectors


def test_retrieval_matches_golden_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    documents = load_markdown_files(DOCUMENTS_DIRECTORY)
    chunks = split_documents(documents)
    cases = evaluation.load_evaluation_cases(QUESTIONS_PATH)
    document_vectors, question_vectors = load_golden_vectors()

    assert {str(document.path) for document in documents} == set(document_vectors)
    assert {case.question for case in cases} == set(question_vectors)

    def load_golden_document_embeddings(
        _client: OpenAI,
        chunks: list[DocumentChunk],
        _cache_path: Path,
    ) -> list[EmbeddedChunk]:
        return [
            EmbeddedChunk(
                chunk=chunk,
                embedding=document_vectors[str(chunk.document_path)],
            )
            for chunk in chunks
        ]

    def load_golden_question_embeddings(
        _client: OpenAI,
        texts: list[str],
    ) -> list[list[float]]:
        return [question_vectors[text] for text in texts]

    monkeypatch.setattr(
        evaluation,
        "load_or_create_embeddings",
        load_golden_document_embeddings,
    )
    monkeypatch.setattr(
        evaluation,
        "create_embeddings",
        load_golden_question_embeddings,
    )

    summary = evaluation.evaluate_retrieval(
        Mock(),
        cases,
        chunks,
        limit=3,
        documents_directory=DOCUMENTS_DIRECTORY,
    )

    assert all(result.hit for result in summary.results)
    assert summary.hit_rate == 1.0
