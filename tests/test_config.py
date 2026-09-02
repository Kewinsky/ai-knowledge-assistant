from pathlib import Path

import pytest

from knowledge_assistant.config import AppConfig, load_config


CONFIG_VARIABLES = (
    "KNOWLEDGE_DOCUMENTS_DIR",
    "KNOWLEDGE_CACHE_PATH",
    "KNOWLEDGE_RESULT_LIMIT",
    "KNOWLEDGE_MIN_SIMILARITY_SCORE",
)


@pytest.fixture(autouse=True)
def clear_config_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in CONFIG_VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def test_load_config_returns_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_config()

    assert config == AppConfig(
        documents_directory=Path("documents"),
        cache_path=Path(".cache/embeddings.json"),
        result_limit=3,
        min_similarity_score=0.5,
    )


def test_load_config_returns_custom_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_DOCUMENTS_DIR", "custom-documents")
    monkeypatch.setenv(
        "KNOWLEDGE_CACHE_PATH",
        "custom-cache/embeddings.json",
    )
    monkeypatch.setenv("KNOWLEDGE_RESULT_LIMIT", "5")
    monkeypatch.setenv("KNOWLEDGE_MIN_SIMILARITY_SCORE", "0.75")

    config = load_config()

    assert config == AppConfig(
        documents_directory=Path("custom-documents"),
        cache_path=Path("custom-cache/embeddings.json"),
        result_limit=5,
        min_similarity_score=0.75,
    )


def test_empty_documents_directory_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_DOCUMENTS_DIR", "   ")

    with pytest.raises(
        ValueError,
        match="KNOWLEDGE_DOCUMENTS_DIR must not be empty",
    ):
        load_config()


def test_empty_cache_path_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_CACHE_PATH", "   ")

    with pytest.raises(
        ValueError,
        match="KNOWLEDGE_CACHE_PATH must not be empty",
    ):
        load_config()


def test_non_integer_result_limit_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_RESULT_LIMIT", "invalid")

    with pytest.raises(
        ValueError,
        match="KNOWLEDGE_RESULT_LIMIT must be a positive integer",
    ):
        load_config()


@pytest.mark.parametrize("value", ["0", "-1"])
def test_non_positive_result_limit_is_rejected(
    value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_RESULT_LIMIT", value)

    with pytest.raises(
        ValueError,
        match="KNOWLEDGE_RESULT_LIMIT must be a positive integer",
    ):
        load_config()


def test_non_numeric_similarity_score_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_MIN_SIMILARITY_SCORE", "invalid")

    with pytest.raises(
        ValueError,
        match="KNOWLEDGE_MIN_SIMILARITY_SCORE must be a number",
    ):
        load_config()


@pytest.mark.parametrize("value", ["-1.1", "1.1"])
def test_out_of_range_similarity_score_is_rejected(
    value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_MIN_SIMILARITY_SCORE", value)

    with pytest.raises(
        ValueError,
        match=(
            "KNOWLEDGE_MIN_SIMILARITY_SCORE must be between -1.0 and 1.0"
        ),
    ):
        load_config()
