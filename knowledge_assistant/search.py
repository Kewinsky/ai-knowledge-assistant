import re

from knowledge_assistant.models import DocumentChunk, SearchResult


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
