import pickle
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "models", "db.pkl")

def save_db(db, path=DB_PATH):
    """Save the embedding database to a pickle file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(db, f)

def load_db(path=DB_PATH):
    """Load the embedding database from a pickle file."""
    if not os.path.exists(path):
        print(f"Warning: Database file {path} not found. Returning empty list.")
        return []
    with open(path, "rb") as f:
        return pickle.load(f)
