#!/Users/donyin/miniconda3/envs/flashcard/bin/python
"""
find similar items using embeddings
"""

from pathlib import Path
import hashlib, json, numpy
from src.modules.dataset import FlashCardDataset
from scipy.spatial.distance import cosine
from src.api.bot import client


def string_to_unique_key(input_string):
    """Converts a string to a unique key using SHA-256 hashing."""
    return hashlib.sha256(input_string.encode()).hexdigest()


def get_embedding(input_string) -> list:
    response = client.embeddings.create(input=input_string, model="text-embedding-ada-002")
    return response.data[0].embedding


class DatasetEmbeddingHandler:
    def __init__(self, dataset: FlashCardDataset):
        """
        1. function 1: use item idx to find embedding
            embedding_handler[0]
        2. function 2: use embedding to find item
            item = embedding_handler.find_similar_item("what is white matter")
            print(item.item_dict)
        """
        self.dataset = dataset
        self.path_embedding = dataset.data_path.parent / f"{self.dataset.dataset_name}.npy"
        self.make_or_read()

    def make_or_read(self):
        if self.path_embedding.exists():
            self.data_embedding = numpy.load(self.path_embedding, allow_pickle=True).item()

        else:  # if not exist make and save
            data = {}
            for item in self.dataset:
                item_hash_str = string_to_unique_key(item.question)
                item_dict_str = json.dumps(item.item_dict, indent=4)
                item_embedding = get_embedding(item_dict_str)
                data.update({item_hash_str: item_embedding})
            self.data_embedding = data
            numpy.save(self.path_embedding, self.data_embedding)

    def find_most_similar_item(self, input_str: str):
        input_embedding = get_embedding(input_string=input_str)
        all_embeddings = numpy.array(list(self.data_embedding.values()))
        all_hashes = list(self.data_embedding.keys())

        distances = numpy.array([cosine(input_embedding, emb) for emb in all_embeddings])
        # min_distance_index = numpy.argmin(distances)
        # find the top 3 most similar items instead
        min_distance_index = numpy.argsort(distances)[:3]

        # return self.hash_str_to_item(all_hashes[min_distance_index])
        return [self.hash_str_to_item(all_hashes[i]) for i in min_distance_index]

    def hash_str_to_item(self, hash_str: str):
        for item in self.dataset:
            if string_to_unique_key(item.question) == hash_str:
                return item
        return None

    def __getitem__(self, idx: int):
        item = self.dataset[idx]
        item_hash_str = string_to_unique_key(item.question)
        return self.data_embedding[item_hash_str]


if __name__ == "__main__":
    dataset = FlashCardDataset(data_path=Path("data", "neuroscience.yaml"))
    embedding_handler = DatasetEmbeddingHandler(dataset=dataset)