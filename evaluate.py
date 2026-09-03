import os
import sys
from pathlib import Path

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from knowledge_assistant.config import load_config
from knowledge_assistant.documents import load_markdown_files, split_documents
from knowledge_assistant.evaluation import (
    evaluate_retrieval,
    load_evaluation_cases,
)


EVALUATION_PATH = Path("evaluation/questions.json")


def main() -> int:
    if len(sys.argv) != 1:
        print("Usage: python3 evaluate.py", file=sys.stderr)
        return 2

    try:
        config = load_config()
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("Error: missing or invalid OpenAI API key.", file=sys.stderr)
        return 1

    try:
        documents = load_markdown_files(config.documents_directory)
        chunks = split_documents(documents)
        cases = load_evaluation_cases(EVALUATION_PATH)
        summary = evaluate_retrieval(
            OpenAI(),
            cases,
            chunks,
            limit=config.result_limit,
            cache_path=config.cache_path,
            documents_directory=config.documents_directory,
        )
    except AuthenticationError:
        print("Error: missing or invalid OpenAI API key.", file=sys.stderr)
        return 1
    except RateLimitError:
        print("Error: OpenAI rate limit exceeded. Try again later.", file=sys.stderr)
        return 1
    except APIConnectionError:
        print("Error: could not connect to OpenAI API.", file=sys.stderr)
        return 1
    except APIStatusError:
        print("Error: OpenAI API request failed.", file=sys.stderr)
        return 1
    except OpenAIError:
        print("Error: OpenAI client configuration failed.", file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("Error: could not run retrieval evaluation.", file=sys.stderr)
        return 1

    for result in summary.results:
        status = "PASS" if result.hit else "FAIL"
        print(f"{status}: {result.case.question}")
        print(f"Expected: {result.case.expected_source}")
        print("Retrieved:")
        for source in result.retrieved_sources:
            print(f"- {source}")
        print()

    hit_count = sum(result.hit for result in summary.results)
    hit_percentage = summary.hit_rate * 100
    print(
        f"Hit@{config.result_limit}: "
        f"{hit_count}/{len(summary.results)} ({hit_percentage:.1f}%)"
    )

    return 0 if hit_count == len(summary.results) else 1


if __name__ == "__main__":
    sys.exit(main())
