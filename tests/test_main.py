import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

import main as cli
from knowledge_assistant.config import AppConfig
from knowledge_assistant.models import (
    Document,
    DocumentChunk,
    RagAnswer,
    SemanticSearchResult,
)


DEFAULT_CONFIG = AppConfig(
    documents_directory=Path("documents"),
    cache_path=Path(".cache/embeddings.json"),
    result_limit=3,
    min_similarity_score=0.5,
)


def test_missing_question_returns_usage_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py"])

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Usage: python3 main.py <question>" in captured.err


def test_missing_api_key_returns_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "What is Python?"])
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    openai_mock = Mock()
    monkeypatch.setattr(cli, "load_config", Mock(return_value=DEFAULT_CONFIG))
    monkeypatch.setattr(cli, "OpenAI", openai_mock)

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: missing or invalid OpenAI API key." in captured.err
    openai_mock.assert_not_called()


def test_os_error_is_written_to_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "What is Python?"])
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cli, "load_config", Mock(return_value=DEFAULT_CONFIG))
    monkeypatch.setattr(
        cli,
        "load_markdown_files",
        Mock(side_effect=OSError),
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert (
        "Error: could not read documents or write embedding cache."
        in captured.err
    )


def test_invalid_config_is_written_to_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "What is Python?"])
    monkeypatch.setattr(
        cli,
        "load_config",
        Mock(
            side_effect=ValueError(
                "KNOWLEDGE_RESULT_LIMIT must be a positive integer"
            )
        ),
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert (
        "Error: KNOWLEDGE_RESULT_LIMIT must be a positive integer"
        in captured.err
    )


def test_success_prints_answer_and_sources_without_chunk_content(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["main.py", "What is Python?"])
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    document = Document(
        path=Path("documents/python.md"),
        content="Full document content",
    )
    chunk = DocumentChunk(
        document_path=document.path,
        index=0,
        content="Full secret chunk content",
    )
    source = SemanticSearchResult(chunk=chunk, score=0.75)
    rag_answer = RagAnswer(
        text="Python is a programming language.",
        sources=[source],
    )
    client = Mock()
    config = AppConfig(
        documents_directory=Path("custom-documents"),
        cache_path=Path("custom-cache/embeddings.json"),
        result_limit=1,
        min_similarity_score=0.6,
    )
    monkeypatch.setattr(cli, "load_config", Mock(return_value=config))
    monkeypatch.setattr(cli, "OpenAI", Mock(return_value=client))
    load_documents_mock = Mock(return_value=[document])
    monkeypatch.setattr(cli, "load_markdown_files", load_documents_mock)
    monkeypatch.setattr(
        cli,
        "split_documents",
        Mock(return_value=[chunk]),
    )
    answer_question_mock = Mock(return_value=rag_answer)
    monkeypatch.setattr(cli, "answer_question", answer_question_mock)

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "Answer:" in captured.out
    assert "Python is a programming language." in captured.out
    assert "Sources:" in captured.out
    assert "documents/python.md#chunk-0 (score: 0.7500)" in captured.out
    assert document.content not in captured.out
    assert chunk.content not in captured.out
    load_documents_mock.assert_called_once_with(Path("custom-documents"))
    answer_question_mock.assert_called_once_with(
        client,
        "What is Python?",
        [chunk],
        limit=1,
        min_similarity_score=0.6,
        cache_path=Path("custom-cache/embeddings.json"),
    )
