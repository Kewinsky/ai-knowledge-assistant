from openai import OpenAI
from openai.types import Embedding

from knowledge_assistant.models import DocumentChunk, EmbeddedChunk


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def create_embeddings(
    client: OpenAI,
    texts: list[str],
) -> list[list[float]]:
    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Texts must not be empty")

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS,
    )

    if len(response.data) != len(texts):
        raise RuntimeError("API returned an unexpected number of embeddings")

    def embedding_index(embedding: Embedding) -> int:
        return embedding.index

    ordered_embeddings = sorted(response.data, key=embedding_index)
    return [item.embedding for item in ordered_embeddings]


def embed_chunks(
    client: OpenAI,
    chunks: list[DocumentChunk],
) -> list[EmbeddedChunk]:
    texts = [chunk.content for chunk in chunks]
    embeddings = create_embeddings(client, texts)
    embedded_chunks: list[EmbeddedChunk] = []

    for chunk, embedding in zip(chunks, embeddings, strict=True):
        embedded_chunks.append(
            EmbeddedChunk(
                chunk=chunk,
                embedding=embedding,
            )
        )

    return embedded_chunks
