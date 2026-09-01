import sys

from openai import OpenAI

from knowledge_assistant.documents import load_markdown_files, split_documents
from knowledge_assistant.embeddings import create_embeddings, embed_chunks
from knowledge_assistant.vector_search import semantic_search


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print("Usage: python3 main.py <question>")
        return

    client = OpenAI()
    documents = load_markdown_files("documents")
    chunks = split_documents(documents)
    embedded_chunks = embed_chunks(client, chunks)
    query_embedding = create_embeddings(client, [query])[0]
    results = semantic_search(query_embedding, embedded_chunks)

    if not results:
        print("No matching documents found.")
    else:
        for result in results:
            print(f"Score: {result.score:.4f}")
            print(f"Source: {result.chunk.document_path}")
            print(f"Chunk: {result.chunk.index}")
            print(result.chunk.content)
            print()


if __name__ == "__main__":
    main()
