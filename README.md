# Celeb Lookalike

A real-time face recognition application that identifies your celebrity lookalike using InsightFace and cosine similarity.

## 🚀 Features

- **Real-time Face Detection**: High-performance face detection using InsightFace.
- **Face Embeddings**: Robust face feature extraction.
- **Fast Matching**: Efficient similarity matching against a database of celebrities.
- **Svelte Frontend**: Modern web interface for real-time lookalike detection.
- **Database Builder**: Easy-to-use script to build your own celebrity database.

## 📁 Project Structure

```
celeb-lookalike/
├── backend/              # Python FastAPI backend
│   ├── app/              # Application logic
│   ├── core/             # Core engines (Face, CLIP, Matcher)
│   ├── data/             # Celebrity images and processed data
│   ├── models/           # Saved embeddings
│   ├── scripts/          # Utility scripts (database builder)
│   ├── main.py           # Entry point
│   └── requirements.txt  # Backend dependencies
├── frontend/             # SvelteKit frontend
├── README.md             # Project overview
└── .gitignore            # Git ignore rules
```

## 🛠️ Setup

### Backend Setup
1. `cd backend`
2. `python -m venv env`
3. `source env/bin/activate` (or `env\Scripts\activate` on Windows)
4. `pip install -r requirements.txt`

### Frontend Setup
1. `cd frontend`
2. `npm install`

## 📖 Usage

### 1. Build the Face Database
Add images to `backend/data/raw/` and run:
```bash
cd backend
python main.py --build
```

### 2. Start the Application
Run the backend server:
```bash
cd backend
python main.py --server
```
Then start the frontend:
```bash
cd frontend
npm run dev
```

## 📜 License
MIT
