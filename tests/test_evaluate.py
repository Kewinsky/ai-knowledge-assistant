import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from openai import OpenAIError

import evaluate as cli
from knowledge_assistant.config import AppConfig
from knowledge_assistant.models import (
    Document,
    DocumentChunk,
    EvaluationCase,
    EvaluationResult,
    EvaluationSummary,
)


CONFIG = AppConfig(
    documents_directory=Path("custom-documents"),
    cache_path=Path("custom-cache/embeddings.json"),
    result_limit=3,
    min_similarity_score=0.5,
)


def test_unexpected_arguments_return_usage_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    load_config_mock = Mock()
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "unexpected"])
    monkeypatch.setattr(cli, "load_config", load_config_mock)

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "Usage: python3 evaluate.py" in captured.err
    load_config_mock.assert_not_called()


def test_missing_api_key_returns_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    openai_mock = Mock()
    monkeypatch.setattr(sys, "argv", ["evaluate.py"])
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli, "load_config", Mock(return_value=CONFIG))
    monkeypatch.setattr(cli, "OpenAI", openai_mock)

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: missing or invalid OpenAI API key." in captured.err
    openai_mock.assert_not_called()


@pytest.mark.parametrize(
    ("hit", "expected_exit_code", "expected_status"),
    [
        (True, 0, "PASS"),
        (False, 1, "FAIL"),
    ],
)
def test_report_and_exit_code_reflect_evaluation_result(
    hit: bool,
    expected_exit_code: int,
    expected_status: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["evaluate.py"])
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    document = Document(
        path=Path("custom-documents/python.md"),
        content="Full document content",
    )
    chunk = DocumentChunk(
        document_path=document.path,
        index=0,
        content="Full secret chunk content",
    )
    case = EvaluationCase(
        question="What is Python?",
        expected_source=Path("documents/python.md"),
    )
    summary = EvaluationSummary(
        results=[
            EvaluationResult(
                case=case,
                retrieved_sources=[Path("documents/python.md")],
                hit=hit,
            )
        ],
        hit_rate=1.0 if hit else 0.0,
    )
    client = Mock()
    load_documents_mock = Mock(return_value=[document])
    split_documents_mock = Mock(return_value=[chunk])
    load_cases_mock = Mock(return_value=[case])
    evaluate_retrieval_mock = Mock(return_value=summary)
    monkeypatch.setattr(cli, "load_config", Mock(return_value=CONFIG))
    monkeypatch.setattr(cli, "OpenAI", Mock(return_value=client))
    monkeypatch.setattr(cli, "load_markdown_files", load_documents_mock)
    monkeypatch.setattr(cli, "split_documents", split_documents_mock)
    monkeypatch.setattr(cli, "load_evaluation_cases", load_cases_mock)
    monkeypatch.setattr(cli, "evaluate_retrieval", evaluate_retrieval_mock)

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == expected_exit_code
    assert captured.err == ""
    assert f"{expected_status}: What is Python?" in captured.out
    assert "Expected: documents/python.md" in captured.out
    assert "- documents/python.md" in captured.out
    expected_percentage = "100.0%" if hit else "0.0%"
    assert f"Hit@3: {int(hit)}/1 ({expected_percentage})" in captured.out
    assert document.content not in captured.out
    assert chunk.content not in captured.out
    load_documents_mock.assert_called_once_with(Path("custom-documents"))
    split_documents_mock.assert_called_once_with([document])
    load_cases_mock.assert_called_once_with(cli.EVALUATION_PATH)
    evaluate_retrieval_mock.assert_called_once_with(
        client,
        [case],
        [chunk],
        limit=3,
        cache_path=Path("custom-cache/embeddings.json"),
        documents_directory=Path("custom-documents"),
    )


@pytest.mark.parametrize(
    ("exception_name", "expected_message"),
    [
        (
            "AuthenticationError",
            "Error: missing or invalid OpenAI API key.",
        ),
        (
            "RateLimitError",
            "Error: OpenAI rate limit exceeded. Try again later.",
        ),
        (
            "APIConnectionError",
            "Error: could not connect to OpenAI API.",
        ),
        (
            "APIStatusError",
            "Error: OpenAI API request failed.",
        ),
        (
            "OpenAIError",
            "Error: OpenAI client configuration failed.",
        ),
    ],
)
def test_openai_errors_are_written_to_stderr(
    exception_name: str,
    expected_message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class TestOpenAIError(OpenAIError):
        pass

    monkeypatch.setattr(sys, "argv", ["evaluate.py"])
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(cli, "load_config", Mock(return_value=CONFIG))
    monkeypatch.setattr(cli, "OpenAI", Mock(return_value=Mock()))
    monkeypatch.setattr(cli, "load_markdown_files", Mock(return_value=[]))
    monkeypatch.setattr(cli, "split_documents", Mock(return_value=[]))
    monkeypatch.setattr(cli, "load_evaluation_cases", Mock(return_value=[]))
    monkeypatch.setattr(cli, exception_name, TestOpenAIError)
    monkeypatch.setattr(
        cli,
        "evaluate_retrieval",
        Mock(side_effect=TestOpenAIError("request failed")),
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert expected_message in captured.err
