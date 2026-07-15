from app.services.rag_vector_service import rag_service_db
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
        
        
        search_data = rag_service_db.search(
            query=embedding,
            k=k,
        )

        results = search_data["results"]

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

        return {
            "answer": answer,
            "sources": sources,
            "benchmark": {
                "algorithm": search_data["algorithm"],
                "time_ms": search_data["time_ms"],
                "vector_count": search_data["vector_count"],
            }
        }


rag_service = RAGService()