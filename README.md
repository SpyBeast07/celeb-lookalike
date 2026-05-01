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

### Backend Setup (Python 3.10 recommended)
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
3. Activate the virtual environment:
   - **Mac/Linux**: `source venv/bin/activate`
   - **Windows**: `venv\Scripts\activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## 📖 Usage

### 1. Build the Face Database
Add celebrity images to `backend/data/raw/` (each celebrity in their own folder) and run:
```bash
cd backend
./venv/bin/python main.py --build
```

### 2. Sanitize Images (Optional)
If you see warnings like "Corrupt JPEG data" during the build process, you can sanitize your images to fix metadata issues:
```bash
cd backend
./venv/bin/python main.py --clean
```

### 3. Start the Backend Server
```bash
cd backend
./venv/bin/python main.py --server
```

### 3. Start the Frontend
```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`.

## 📜 License
MIT
