import json
from pathlib import Path

from openai import OpenAI

from knowledge_assistant.embedding_cache import load_or_create_embeddings
from knowledge_assistant.embeddings import create_embeddings
from knowledge_assistant.models import (
    DocumentChunk,
    EvaluationCase,
    EvaluationResult,
    EvaluationSummary,
)
from knowledge_assistant.vector_search import semantic_search


CANONICAL_DOCUMENTS_DIRECTORY = Path("documents")


def _canonical_source_path(
    source_path: Path,
    documents_directory: Path,
) -> Path:
    try:
        relative_path = source_path.relative_to(documents_directory)
    except ValueError as error:
        raise ValueError(
            f"Source path must be inside documents directory: {source_path}"
        ) from error

    return CANONICAL_DOCUMENTS_DIRECTORY / relative_path


def load_evaluation_cases(path: str | Path) -> list[EvaluationCase]:
    with Path(path).open(encoding="utf-8") as evaluation_file:
        try:
            data: object = json.load(evaluation_file)
        except json.JSONDecodeError as error:
            raise ValueError("Evaluation file must contain valid JSON") from error

    if not isinstance(data, list) or not data:
        raise ValueError("Evaluation cases must be a non-empty list")

    cases: list[EvaluationCase] = []

    for record in data:
        if not isinstance(record, dict):
            raise ValueError("Each evaluation case must be an object")

        question = record.get("question")
        expected_source = record.get("expected_source")

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Evaluation question must be a non-empty string")

        if not isinstance(expected_source, str) or not expected_source.strip():
            raise ValueError(
                "Evaluation expected_source must be a non-empty string"
            )

        cases.append(
            EvaluationCase(
                question=question.strip(),
                expected_source=Path(expected_source.strip()),
            )
        )

    return cases


def evaluate_retrieval(
    client: OpenAI,
    cases: list[EvaluationCase],
    chunks: list[DocumentChunk],
    limit: int = 3,
    cache_path: Path = Path(".cache/embeddings.json"),
    documents_directory: Path = CANONICAL_DOCUMENTS_DIRECTORY,
) -> EvaluationSummary:
    if not cases:
        raise ValueError("Evaluation cases must not be empty")

    if not chunks:
        raise ValueError("Chunks must not be empty")

    if limit <= 0:
        raise ValueError("Limit must be greater than zero")

    embedded_chunks = load_or_create_embeddings(client, chunks, cache_path)
    question_embeddings = create_embeddings(
        client,
        [case.question for case in cases],
    )
    results: list[EvaluationResult] = []

    for case, question_embedding in zip(
        cases,
        question_embeddings,
        strict=True,
    ):
        expected_source = _canonical_source_path(
            case.expected_source,
            CANONICAL_DOCUMENTS_DIRECTORY,
        )
        search_results = semantic_search(
            question_embedding,
            embedded_chunks,
            limit,
        )
        retrieved_sources = list(
            dict.fromkeys(
                _canonical_source_path(
                    result.chunk.document_path,
                    documents_directory,
                )
                for result in search_results
            )
        )
        results.append(
            EvaluationResult(
                case=case,
                retrieved_sources=retrieved_sources,
                hit=expected_source in retrieved_sources,
            )
        )

    hit_count = sum(result.hit for result in results)
    return EvaluationSummary(
        results=results,
        hit_rate=hit_count / len(results),
    )
