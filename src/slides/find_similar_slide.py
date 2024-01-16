#!/Users/donyin/miniconda3/envs/flashcard/bin/python
"""
find the most similar slide using embeddings
[currently not integrated in UI]
"""

from pathlib import Path
import pickle, fitz, numpy as np
from scipy.spatial.distance import cosine
from src.slides.find_similar_exam_item import get_embedding
from natsort import natsorted
from rich import print


class SlidesEmbeddingHandler:
    def __init__(self, path_files: Path):
        self.path = path_files
        self.files = natsorted(list(path_files.glob("*.pdf")))
        self.path_embedding = path_files / "embeddings.npy"

    def get_most_similar_slides(self, query: str, top_n=5):
        if not self.path_embedding.exists():
            self._make_embeddings()
        self.embeddings = self._read_embeddings()

        query_embedding = get_embedding(query)
        embeddings_array = np.array([emb[2] for emb in self.embeddings])
        distances = np.array([cosine(query_embedding, emb) for emb in embeddings_array])
        min_distance_indices = np.argsort(distances)[:top_n]
        return [self.embeddings[idx][:2] for idx in min_distance_indices]

    # ---- [making and reading embeddings] ----
    def _make_embeddings(self):
        embeddings = []
        for file in self.files:
            doc = fitz.open(file)
            for page_num in range(len(doc)):
                print(f"Processing {file} page {page_num}")
                page = doc.load_page(page_num)
                text = page.get_text()
                slide_embedding = get_embedding(text)
                embeddings.append((file, page_num, slide_embedding))
            doc.close()
        with open(self.path_embedding, "wb") as f:
            pickle.dump(embeddings, f)

    def _read_embeddings(self):
        with open(self.path_embedding, "rb") as f:
            return pickle.load(f)


if __name__ == "__main__":
    path = Path("/Users/donyin/Dropbox/~desktop/modules/neuroscience/lectures/")
    handler = SlidesEmbeddingHandler(path)
    while True:
        query = input("Enter query: ")
        if query == "exit":
            break
        similar_slides = handler.get_most_similar_slides(query, 5)
        for idx, (file, page) in enumerate(similar_slides):
            print(f"Similar slide {idx+1}: {file.name} page {page}")
