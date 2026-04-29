# Celeb Lookalike

A real-time face recognition application that identifies your celebrity lookalike using InsightFace and cosine similarity.

## 🚀 Features

- **Real-time Face Detection**: High-performance face detection using InsightFace.
- **Face Embeddings**: Robust face feature extraction.
- **Fast Matching**: Efficient similarity matching against a database of celebrities.
- **Database Builder**: Easy-to-use script to build your own celebrity database from raw images.

## 📁 Project Structure

```
celeb-lookalike/
├── data/
│   ├── raw/              # Place your celebrity images here (organized by folder)
│   └── processed/        # Cleaned dataset (optional)
├── models/               # Saved embeddings (e.g., embeddings.pkl)
├── core/
│   ├── face_engine.py    # InsightFace initialization and detection
│   ├── clip_engine.py    # CLIP embeddings for multimodal search (future)
│   ├── matcher.py        # Cosine similarity matching logic
│   └── database.py       # Load/Save operations for embeddings
├── app/
│   └── webcam.py         # Real-time webcam UI
├── scripts/
│   └── build_db.py       # Script to build the embedding database
├── requirements.txt
└── main.py               # Main entry point
```

## 🛠️ Environment Setup

1. **Create and Activate Environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Usage

### 1. Prepare Celebrity Data
Add images to `celeb-lookalike/data/raw/` in the following format:
```
data/raw/
├── Celebrity Name 1/
│   ├── image1.jpg
│   └── image2.jpg
└── Celebrity Name 2/
    ├── image1.jpg
    └── image2.jpg
```

### 2. Build the Face Database
This script processes the raw images and saves embeddings to `models/embeddings.pkl`.
```bash
python main.py --build
```

### 3. Start the Webcam App
Identify your celebrity lookalike in real-time!
```bash
python main.py --run
```

## 📜 License
MIT
