from openai import OpenAI

from knowledge_assistant.embeddings import create_embeddings, embed_chunks
from knowledge_assistant.generation import generate_answer
from knowledge_assistant.models import DocumentChunk, RagAnswer
from knowledge_assistant.vector_search import semantic_search


def answer_question(
    client: OpenAI,
    question: str,
    chunks: list[DocumentChunk],
    limit: int = 3,
) -> RagAnswer:
    stripped_question = question.strip()

    if not stripped_question:
        raise ValueError("Question must not be empty")

    if not chunks:
        raise ValueError("Chunks must not be empty")

    if limit <= 0:
        raise ValueError("Limit must be greater than zero")

    embedded_chunks = embed_chunks(client, chunks)
    query_embedding = create_embeddings(client, [stripped_question])[0]
    results = semantic_search(query_embedding, embedded_chunks, limit)
    answer = generate_answer(client, stripped_question, results)

    return RagAnswer(
        text=answer,
        sources=results,
    )
