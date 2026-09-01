from openai import OpenAI

from knowledge_assistant.embedding_cache import load_or_create_embeddings
from knowledge_assistant.embeddings import create_embeddings
from knowledge_assistant.generation import generate_answer
from knowledge_assistant.models import DocumentChunk, RagAnswer
from knowledge_assistant.vector_search import semantic_search


MIN_SIMILARITY_SCORE = 0.5
INSUFFICIENT_CONTEXT_ANSWER = "I don't know based on the available documents."


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

    embedded_chunks = load_or_create_embeddings(client, chunks)
    query_embedding = create_embeddings(client, [stripped_question])[0]
    results = semantic_search(query_embedding, embedded_chunks, limit)
    relevant_results = [
        result for result in results if result.score >= MIN_SIMILARITY_SCORE
    ]

    if not relevant_results:
        return RagAnswer(
            text=INSUFFICIENT_CONTEXT_ANSWER,
            sources=[],
        )

    answer = generate_answer(client, stripped_question, relevant_results)

    return RagAnswer(
        text=answer,
        sources=relevant_results,
    )
