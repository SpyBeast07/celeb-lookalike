import requests
import base64
import os

def encode_image(image_path):
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def ask_ollama(image_path, model="gemma4:e4b"):
    url = "http://192.168.29.120:11434/api/generate"
    
    image_base64 = encode_image(image_path)
    if not image_base64:
        return

    payload = {
        "model": model,
        "prompt": "You are a celebrity look-alike expert. Analyze the attached image and determine which celebrity this person looks like most. Be decisive. Provide the celebrity's name and a similarity percentage (e.g., 85%). This is for a fun 'Celebrity Look-alike Cam' app. Format your response clearly like this:\n\nCelebrity: [Name]\nSimilarity: [Percentage]%\nReasoning: [Brief explanation]",
        "images": [image_base64],
        "stream": False
    }

    print(f"Sending request to Ollama at {url} using model {model}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("\nResponse from AI:")
        print(result.get("response", "No response found in the output."))
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")

if __name__ == "__main__":
    test_image = "test.jpg"
    ask_ollama(test_image)
