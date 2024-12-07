import requests
import os
import json

def test_upload_image():
    print("Starting test...\n")

    # Test image path
    test_image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'abra.png')
    print(f"Testing with image: {test_image_path}")
    print(f"Image exists: {os.path.exists(test_image_path)}")

    # URL for the upload endpoint
    url = "https://flask-backend-150344248755.europe-west1.run.app/upload-image"
    print(f"Making request to: {url}\n")

    # Open the image file
    with open(test_image_path, 'rb') as f:
        # Create the files payload
        files = {'image': ('abra.png', f, 'image/png')}
        
        # Make the POST request
        response = requests.post(url, files=files)
    
    print("Upload Image Endpoint:")
    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        result = response.json()
        print("Response:")
        print(f"Detected: {result.get('detected', False)}")
        print(f"Predicted Pokemon: {result.get('predicted_pokemon', 'None')}")
        print(f"Pokemon image included: {bool(result.get('pokemon_image'))}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_upload_image()
