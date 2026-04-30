import sys
import argparse
from scripts.build_db import build_database
from app.webcam import start_webcam

def main():
    parser = argparse.ArgumentParser(description="Celeb Lookalike Application")
    parser.add_argument("--build", action="store_true", help="Build the embedding database")
    parser.add_argument("--data", type=str, default="data/raw", help="Path to raw data for building database")
    parser.add_argument("--run", action="store_true", help="Start the webcam app")
    parser.add_argument("--server", action="store_true", help="Start the FastAPI server")
    
    args = parser.parse_args()
    
    if args.build:
        build_database(args.data)
    elif args.run:
        start_webcam()
    elif args.server:
        import uvicorn
        from api import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
