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
