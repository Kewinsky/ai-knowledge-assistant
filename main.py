import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Document:
    path: Path
    content: str


@dataclass
class DocumentChunk:
    document_path: Path
    index: int
    content: str


@dataclass
class SearchResult:
    chunk: DocumentChunk
    score: int


def load_markdown_files(directory: str | Path) -> list[Document]:
    directory_path = Path(directory)

    if not directory_path.is_dir():
        raise NotADirectoryError(f"Expected an existing directory: {directory_path}")

    documents: list[Document] = []

    for file_path in sorted(directory_path.rglob("*.md")):
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8")
            documents.append(Document(path=file_path, content=content))

    return documents


def split_document(document: Document) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []

    for part in document.content.split("\n\n"):
        content = part.strip()

        if content:
            chunks.append(
                DocumentChunk(
                    document_path=document.path,
                    index=len(chunks),
                    content=content,
                )
            )

    return chunks


def split_documents(documents: list[Document]) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []

    for document in documents:
        chunks.extend(split_document(document))

    return chunks


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def score_chunk(query_tokens: set[str], chunk: DocumentChunk) -> int:
    chunk_tokens = tokenize(chunk.content)
    return len(query_tokens & chunk_tokens)


def search_chunks(
    query: str,
    chunks: list[DocumentChunk],
    limit: int = 3,
) -> list[SearchResult]:
    if limit <= 0:
        return []

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    results: list[SearchResult] = []

    for chunk in chunks:
        score = score_chunk(query_tokens, chunk)

        if score > 0:
            results.append(SearchResult(chunk, score))

    def sort_key(result: SearchResult) -> tuple[int, str, int]:
        return (
            -result.score,
            str(result.chunk.document_path),
            result.chunk.index,
        )

    results.sort(key=sort_key)

    return results[:limit]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print("Usage: python3 main.py <question>")
    else:
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
