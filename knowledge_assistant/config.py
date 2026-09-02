import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    documents_directory: Path
    cache_path: Path
    result_limit: int
    min_similarity_score: float


def load_config() -> AppConfig:
    documents_directory_value = os.environ.get(
        "KNOWLEDGE_DOCUMENTS_DIR",
        "documents",
    ).strip()
    cache_path_value = os.environ.get(
        "KNOWLEDGE_CACHE_PATH",
        ".cache/embeddings.json",
    ).strip()
    result_limit_value = os.environ.get("KNOWLEDGE_RESULT_LIMIT", "3").strip()
    min_similarity_score_value = os.environ.get(
        "KNOWLEDGE_MIN_SIMILARITY_SCORE",
        "0.5",
    ).strip()

    if not documents_directory_value:
        raise ValueError("KNOWLEDGE_DOCUMENTS_DIR must not be empty")

    if not cache_path_value:
        raise ValueError("KNOWLEDGE_CACHE_PATH must not be empty")

    try:
        result_limit = int(result_limit_value)
    except ValueError as error:
        raise ValueError(
            "KNOWLEDGE_RESULT_LIMIT must be a positive integer"
        ) from error

    if result_limit <= 0:
        raise ValueError("KNOWLEDGE_RESULT_LIMIT must be a positive integer")

    try:
        min_similarity_score = float(min_similarity_score_value)
    except ValueError as error:
        raise ValueError(
            "KNOWLEDGE_MIN_SIMILARITY_SCORE must be a number"
        ) from error

    if not -1.0 <= min_similarity_score <= 1.0:
        raise ValueError(
            "KNOWLEDGE_MIN_SIMILARITY_SCORE must be between -1.0 and 1.0"
        )

    return AppConfig(
        documents_directory=Path(documents_directory_value),
        cache_path=Path(cache_path_value),
        result_limit=result_limit,
        min_similarity_score=min_similarity_score,
    )
