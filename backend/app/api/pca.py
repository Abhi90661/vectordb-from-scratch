from fastapi import APIRouter
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.services.vector_service import service

router = APIRouter()



@router.get("/pca")
def get_pca():

    vectors = list(service.get_all_vectors())

    if len(vectors) < 2:
        return {
            "points": [],
            "total_vectors": 0,
            "dimensions": 0,
            "explained_variance": 0,
        }

    X = [v.vector for v in vectors]

    # Normalize every dimension
    X = StandardScaler().fit_transform(X)

    # Create PCA object
    pca = PCA(n_components=2)

    # Transform vectors
    coords = pca.fit_transform(X)

    explained_variance = float(
        pca.explained_variance_ratio_.sum() * 100
    )

    return {
        "points": [
            {
                "id": vectors[i].id,
                "x": float(coords[i][0]),
                "y": float(coords[i][1]),
                "metadata": vectors[i].metadata,
            }
            for i in range(len(vectors))
        ],
        "total_vectors": len(vectors),
        "dimensions": len(vectors[0].vector),
        "explained_variance": explained_variance,
    }