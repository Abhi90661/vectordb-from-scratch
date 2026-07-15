from fastapi import APIRouter, UploadFile, File
import csv
import io

from app.models.vector import VectorItem
from app.services.vector_service import service

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)):

    # Read uploaded CSV
    content = await file.read()
    text = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))

    # Clear existing vectors
    service.clear()

    vectors = []

    for row in reader:

        vectors.append(
            VectorItem(
                id=row["id"],
                vector=[float(x) for x in row["vector"].split(",")],
                metadata={
                    "category": row["category"],
                },
            )
        )

    service.bulk_insert(vectors)

    print("=" * 50)
    print("CSV Upload Complete")
    print("Rows Processed :", len(vectors))
    print("Vectors Stored :", service.size())
    print("=" * 50)

    return {
        "message": "CSV imported successfully",
        "rows_imported": len(vectors),
        "total_vectors": service.size(),
    }