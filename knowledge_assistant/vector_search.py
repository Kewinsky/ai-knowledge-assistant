import math

from knowledge_assistant.models import EmbeddedChunk, SemanticSearchResult


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have the same length")

    if not left:
        raise ValueError("Vectors must not be empty")

    dot_product = sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )
    left_magnitude = math.sqrt(sum(value**2 for value in left))
    right_magnitude = math.sqrt(sum(value**2 for value in right))

    if left_magnitude == 0 or right_magnitude == 0:
        raise ValueError("Vectors must not have zero magnitude")

    return dot_product / (left_magnitude * right_magnitude)


def semantic_search(
    query_embedding: list[float],
    embedded_chunks: list[EmbeddedChunk],
    limit: int = 3,
) -> list[SemanticSearchResult]:
    if limit <= 0 or not embedded_chunks:
        return []

    results: list[SemanticSearchResult] = []

    for embedded_chunk in embedded_chunks:
        score = cosine_similarity(query_embedding, embedded_chunk.embedding)
        results.append(
            SemanticSearchResult(
                chunk=embedded_chunk.chunk,
                score=score,
            )
        )

    def sort_key(result: SemanticSearchResult) -> tuple[float, str, int]:
        return (
            -result.score,
            str(result.chunk.document_path),
            result.chunk.index,
        )

    results.sort(key=sort_key)
    return results[:limit]
