import sys
import argparse
from scripts.build_db import build_database
from app.webcam import start_webcam

def main():
    parser = argparse.ArgumentParser(description="Celeb Lookalike Application")
    parser.add_argument("--build", action="store_true", help="Build the embedding database")
    parser.add_argument("--data", type=str, default="data/raw", help="Path to raw data for building database")
    parser.add_argument("--run", action="store_true", help="Start the webcam app")
    
    args = parser.parse_args()
    
    if args.build:
        build_database(args.data)
    elif args.run:
        start_webcam()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
