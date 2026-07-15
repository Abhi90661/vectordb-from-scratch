from fastapi import APIRouter
from sklearn.decomposition import PCA

from app.services.vector_service import service

router = APIRouter()


@router.get("/visualize")
def visualize():

    vectors = service.get_all_vectors().copy()

    if len(vectors) < 2:
        return []

    matrix = [v.vector for v in vectors]

    pca = PCA(n_components=2)

    coords = pca.fit_transform(matrix)

    result = []

    for i, item in enumerate(vectors):
        result.append({
            "id": item.id,
            "x": float(coords[i][0]),
            "y": float(coords[i][1]),
            "metadata": item.metadata,
        })

    return result