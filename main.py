import sys

from knowledge_assistant.documents import load_markdown_files, split_documents
from knowledge_assistant.search import search_chunks


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print("Usage: python3 main.py <question>")
        return

    documents = load_markdown_files("documents")
    chunks = split_documents(documents)
    results = search_chunks(query, chunks)

    if not results:
        print("No matching documents found.")
    else:
        for result in results:
            print(f"Score: {result.score}")
            print(f"Source: {result.chunk.document_path}")
            print(f"Chunk: {result.chunk.index}")
            print(result.chunk.content)
            print()


if __name__ == "__main__":
    main()
