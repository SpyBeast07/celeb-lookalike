import cv2
from core.face_engine import get_faces
from core.matcher import find_top_k
from core.database import load_db

def start_webcam():
    print("Loading database...")
    db = load_db()
    if not db:
        print("Error: Database is empty. Please run 'scripts/build_db.py' first.")
        return

    print("Starting webcam... Press ESC to exit.")
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        faces = get_faces(frame)
        for face in faces:
            emb = face.embedding
            results = find_top_k(emb, db)
            
            # Draw bounding box
            bbox = face.bbox.astype(int)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            
            # Show results
            y = int(bbox[1])
            for i, (name, score) in enumerate(results):
                text = f"{name}: {score:.2f}"
                cv2.putText(frame, text,
                            (int(bbox[0]), y - 10 - i*20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 1)
        
        cv2.imshow("Lookalike Cam", frame)
        if cv2.waitKey(1) == 27: # ESC key
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_webcam()
