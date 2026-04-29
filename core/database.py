import pickle
import os

class Database:
    def __init__(self, db_path='models/embeddings.pkl'):
        self.db_path = db_path

    def save(self, embeddings, labels):
        with open(self.db_path, 'wb') as f:
            pickle.dump({'embeddings': embeddings, 'labels': labels}, f)

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f:
                return pickle.load(f)
        return None
