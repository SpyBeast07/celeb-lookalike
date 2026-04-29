import pickle
import os

def save_db(db, path="models/db.pkl"):
    """Save the embedding database to a pickle file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(db, f)

def load_db(path="models/db.pkl"):
    """Load the embedding database from a pickle file."""
    if not os.path.exists(path):
        print(f"Warning: Database file {path} not found. Returning empty list.")
        return []
    with open(path, "rb") as f:
        return pickle.load(f)
