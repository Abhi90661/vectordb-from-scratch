import ollama


class LLMService:

    def generate(self, context: str, question: str):

        prompt = f"""
You are a helpful AI assistant.

Answer ONLY using the information in the context below.

If the answer is not present in the context, say:
"I couldn't find that information in the uploaded documents."

Context:
{context}

Question:
{question}

Answer:
"""

        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response["message"]["content"]


llm_service = LLMService()