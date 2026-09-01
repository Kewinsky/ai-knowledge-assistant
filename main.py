import sys

from openai import OpenAI

from knowledge_assistant.documents import load_markdown_files, split_documents
from knowledge_assistant.rag import answer_question


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print("Usage: python3 main.py <question>")
        return

    documents = load_markdown_files("documents")
    chunks = split_documents(documents)
    client = OpenAI()
    rag_answer = answer_question(
        client,
        query,
        chunks,
    )

    print("Answer:")
    print(rag_answer.text)
    print()
    print("Sources:")

    for result in rag_answer.sources:
        chunk = result.chunk
        print(
            f"- {chunk.document_path}#chunk-{chunk.index} "
            f"(score: {result.score:.4f})"
        )


if __name__ == "__main__":
    main()
