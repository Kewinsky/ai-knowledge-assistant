from dataclasses import dataclass
from pathlib import Path


@dataclass
class Document:
    path: Path
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
