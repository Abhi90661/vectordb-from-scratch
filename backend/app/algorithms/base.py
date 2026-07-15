from abc import ABC, abstractmethod
from app.models.vector import VectorItem


class BaseIndex(ABC):

    @abstractmethod
    def insert(self, item: VectorItem):
        pass

    @abstractmethod
    def delete(self, vector_id: str):
        pass

    @abstractmethod
    def search(self, query, k=5, metric="cosine"):
        pass

    @abstractmethod
    def size(self):
        pass