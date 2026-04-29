import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class Matcher:
    def __init__(self, database_embeddings, database_labels):
        self.database_embeddings = database_embeddings
        self.database_labels = database_labels

    def find_best_match(self, query_embedding):
        similarities = cosine_similarity([query_embedding], self.database_embeddings)
        best_idx = np.argmax(similarities)
        return self.database_labels[best_idx], similarities[0][best_idx]
