import json
from pathlib import Path

from app.algorithms.brute_force import BruteForceIndex
from app.algorithms.hnsw import HNSWIndex
from app.algorithms.ivf import IVFIndex
from app.algorithms.kd_tree import KDTreeIndex
from app.models.vector import VectorItem

VECTOR_FILE = Path("storage/vectors.json")


class VectorService:

    def __init__(self):
        print("VectorService initialized")

        self.index = BruteForceIndex()

        if VECTOR_FILE.exists():
            print("Loading vectors from disk...")
            self.load_database(VECTOR_FILE)
        
    

    def insert(
        self,
        id: str,
        vector: list[float],
        metadata: dict,
        save: bool = True,
    ):
        item = VectorItem(
            id=id,
            vector=vector,
            metadata=metadata,
        )

        self.index.insert(item)

        if save:
            self.save_database()

    def bulk_insert(self, vectors):

        for vector in vectors:

            item = VectorItem(
                id=vector.id,
                vector=vector.vector,
                metadata=vector.metadata,
            )

            self.index.insert(item)

        if hasattr(self.index, "rebuild"):
            self.index.rebuild()

        # Save only once
        self.save_database()

    def search(self, query, k, filter=None):
        results = self.index.search(query, k=k)

        if filter:
            filtered = []

            for item, distance in results:
                matched = True

                for key, value in filter.items():

                    item_value = item.metadata.get(key)

                    if isinstance(value, dict):

                        if "$gt" in value and not (item_value > value["$gt"]):
                            matched = False
                            break

                        if "$gte" in value and not (item_value >= value["$gte"]):
                            matched = False
                            break

                        if "$lt" in value and not (item_value < value["$lt"]):
                            matched = False
                            break

                        if "$lte" in value and not (item_value <= value["$lte"]):
                            matched = False
                            break

                        if "$ne" in value and not (item_value != value["$ne"]):
                            matched = False
                            break

                        if "$in" in value and item_value not in value["$in"]:
                            matched = False
                            break

                    else:

                        if item_value != value:
                            matched = False
                            break

                if matched:
                    filtered.append((item, distance))

            results = filtered

        return results[:k]

    def delete(self, id: str):
        try:
            self.index.delete(id)
            self.save_database()
            return True
        except Exception:
            return False

    def size(self):
        return self.index.size()

    def set_index(self, index_type: str):
        


        print("Before set_index:", self.index.__class__.__name__, self.size())
        
        old_vectors = list(self.get_all_vectors())

        index_type = index_type.lower()

        if index_type == "bruteforce":
            # NOTE: previously `self.index.__class__()`, which re-instantiated
            # whatever class self.index already was (e.g. switching from IVF
            # to "bruteforce" silently created a fresh IVFIndex instead of a
            # BruteForceIndex). Explicit is correct here.
            self.index = BruteForceIndex()

        elif index_type == "kdtree":
            self.index = KDTreeIndex()

        elif index_type == "hnsw":
            self.index = HNSWIndex()

        elif index_type == "ivf":
            self.index = IVFIndex()

        else:
            raise ValueError("Invalid index type")
        
        for item in old_vectors:
            self.index.insert(item)

        if hasattr(self.index, "rebuild"):
            self.index.rebuild()

        print("After set_index:", self.index.__class__.__name__, self.size())

        return self.index.__class__.__name__
    
    def get_all_vectors(self):
        # Each index stores its items in a different shape:
        #   BruteForceIndex / KDTreeIndex -> self.items is a List[VectorItem]
        #   IVFIndex                      -> self.items is a Dict[id, VectorItem]
        #   HNSWIndex                     -> has no .items at all; vectors
        #                                     live inside self.nodes, a
        #                                     Dict[id, HNSWNode], where each
        #                                     node wraps the VectorItem as
        #                                     node.item.
        #
        # The previous version only checked for `.items` and returned it
        # as-is. For IVF that returned the dict itself (iterating over it
        # elsewhere yields keys, not VectorItems); for HNSW `.items` didn't
        # exist at all, so this returned [] -- meaning save_database()
        # silently wrote an empty file whenever HNSW was the active index,
        # discarding all inserted vectors on the next load.
        items = getattr(self.index, "items", None)
        if items is not None:
            if isinstance(items, dict):
                return list(items.values())
            return items

        nodes = getattr(self.index, "nodes", None)
        if nodes is not None:
            return [node.item for node in nodes.values()]

        return []

    def save_database(self, filename=VECTOR_FILE):

        vectors = self.get_all_vectors()

        data = [vector.model_dump() for vector in vectors]

        with open(filename, "w") as file:
            json.dump(data, file, indent=4)

        return len(data)
    
    

    def load_database(self, filename=VECTOR_FILE):
        
        print("Loading database...")

        if not Path(filename).exists():
            return 0

        with open(filename, "r") as file:
            data = json.load(file)
        self.index = BruteForceIndex()

        for vector in data:

            item = VectorItem(
                id=vector["id"],
                vector=vector["vector"],
                metadata=vector["metadata"],
            )

            self.index.insert(item)
            

        return len(data)
    
    def clear(self):

        print("Before clear:", self.size())

        if hasattr(self.index, "clear"):
            self.index.clear()
        else:
            self.index = self.index.__class__()

        print("After clear:", self.size())

        self.save_database()
        
        
    def update(self, id: str, vector: list[float], metadata: dict):
        item = VectorItem(
            id=id,
            vector=vector,
            metadata=metadata,
        )

        updated = self.index.update(item)

        if updated:
            self.save_database()

        return updated
    
    def batch_insert(self, vectors):

        inserted = 0

        for vector in vectors:

            item = VectorItem(
                id=vector.id,
                vector=vector.vector,
                metadata=vector.metadata,
            )

            self.index.insert(item)
            inserted += 1

        if hasattr(self.index, "rebuild"):
            self.index.rebuild()

        self.save_database()

        return inserted
    
    def upsert(self, vector_id, vector, metadata):

        item = VectorItem(
            id=vector_id,
            vector=vector,
            metadata=metadata,
        )

        self.index.upsert(item)
        self.save_database()
        
        
service = VectorService()