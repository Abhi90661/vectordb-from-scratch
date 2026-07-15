from app.services.vector_service import service
from app.services.llm_service import llm_service

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


class RAGService:

    def embed_text(self, text: str):
        embedding = model.encode(text)
        return embedding.tolist()

    def answer_question(self, question: str, k: int = 3):

        # Convert question into embedding
        embedding = self.embed_text(question)

        # Retrieve nearest chunks from VectorDB
        results = service.search(
            query=embedding,
            k=k,
        )

        # Combine retrieved chunks into context
        context = "\n\n".join(
            item.metadata["text"]
            for item, _ in results
        )

        # Ask the LLM using retrieved context
        answer = llm_service.generate(
            context=context,
            question=question,
        )

        # Return retrieved sources
        sources = []

        for item, distance in results:

            sources.append(
                {
                    "text": item.metadata["text"],
                    "source": item.metadata["source"],
                    "distance": distance,
                }
            )

        return answer, sources


rag_service = RAGService()