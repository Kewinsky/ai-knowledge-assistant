import os
import sys

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from knowledge_assistant.documents import load_markdown_files, split_documents
from knowledge_assistant.rag import answer_question


def main() -> int:
    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print("Usage: python3 main.py <question>", file=sys.stderr)
        return 2

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("Error: missing or invalid OpenAI API key.", file=sys.stderr)
        return 1

    try:
        documents = load_markdown_files("documents")
        chunks = split_documents(documents)
        client = OpenAI()
        rag_answer = answer_question(
            client,
            query,
            chunks,
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
    except OSError:
        print(
            "Error: could not read documents or write embedding cache.",
            file=sys.stderr,
        )
        return 1

    print("Answer:")
    print(rag_answer.text)

    if rag_answer.sources:
        print()
        print("Sources:")

        for result in rag_answer.sources:
            chunk = result.chunk
            print(
                f"- {chunk.document_path}#chunk-{chunk.index} "
                f"(score: {result.score:.4f})"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
