from app.services.llm_service import llm_service
from fastapi import APIRouter, UploadFile, File
import uuid

from app.services.rag_service import rag_service
from app.services.vector_service import service
from app.services.chat_service import chat_service

from pydantic import BaseModel

router = APIRouter()

class QueryRequest(BaseModel):

    question: str

    k: int = 3
    
class AskRequest(BaseModel):

    chat_id: str

    question: str

    k: int = 3
    
@router.post("/rag/query")

def query_document(request: QueryRequest):

    embedding = rag_service.embed_text(request.question)

    results = service.search(

        query=embedding,

        k=request.k,

    )

    context = "\n\n".join(

        item.metadata["text"]

        for item, _ in results

    )

    answer = llm_service.generate(

        context=context,

        question=request.question,

    )

    return {

        "answer": answer,

        "sources": [

            {

                "source": item.metadata["source"],

                "text": item.metadata["text"],

                "distance": distance,

            }

            for item, distance in results

        ]

    }
    
@router.post("/rag/ask")
def ask_ai(request: AskRequest):

    # Save user's message
    chat_service.add_message(
        request.chat_id,
        "user",
        request.question,
    )

    # Generate answer
    answer, sources = rag_service.answer_question(
        request.question,
        request.k,
    )

    # Save AI response
    chat_service.add_message(
        request.chat_id,
        "assistant",
        answer,
        sources=sources,
    )

    return {
        "answer": answer,
        "sources": sources,
    }




@router.post("/rag/upload")
async def upload_document(file: UploadFile = File(...)):

    # Read uploaded file
    content = await file.read()
    text = content.decode("utf-8")

    # Split into chunks
    chunks = [
        text[i:i+500]
        for i in range(0, len(text), 500)
    ]

    inserted = 0

    for chunk in chunks:

        embedding = rag_service.embed_text(chunk)

        service.insert(
            id=str(uuid.uuid4()),
            vector=embedding,
            metadata={
                "text": chunk,
                "source": file.filename,
            },
        )

        inserted += 1

    return {
        "message": "Document indexed successfully",
        "chunks": inserted,
    }
    
@router.post("/chat/new")
def new_chat():

    return chat_service.new_chat()


@router.get("/chat")
def get_all_chats():

    return chat_service.get_all_chats()


@router.get("/chat/{chat_id}")
def get_chat(chat_id: str):

    chat = chat_service.get_chat(chat_id)

    if chat is None:
        return {
            "message": "Chat not found"
        }

    return chat