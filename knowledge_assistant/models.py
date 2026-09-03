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


@dataclass
class EmbeddedChunk:
    chunk: DocumentChunk
    embedding: list[float]


@dataclass
class SemanticSearchResult:
    chunk: DocumentChunk
    score: float


@dataclass
class RagAnswer:
    text: str
    sources: list[SemanticSearchResult]


@dataclass(frozen=True)
class EvaluationCase:
    question: str
    expected_source: Path


@dataclass
class EvaluationResult:
    case: EvaluationCase
    retrieved_sources: list[Path]
    hit: bool


@dataclass
class EvaluationSummary:
    results: list[EvaluationResult]
    hit_rate: float
