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


if __name__ == "__main__":
    documents = load_markdown_files("documents")
    chunks = split_documents(documents)

    for chunk in chunks:
        print(f"Path: {chunk.document_path}")
        print(f"Index: {chunk.index}")
        print(chunk.content)
        print()
