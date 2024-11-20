import os
from flask import Flask, request, jsonify
from PIL import Image
import torch
from transformers import OwlViTProcessor, OwlViTForObjectDetection
import io

# Initialize Flask app
app = Flask(__name__)

# Load the OWL-ViT model and processor
od_model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")
od_processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
od_model.to(device)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/detect', methods=['POST', 'OPTIONS'])
def detect():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    # Check if the request contains an image
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    try:
        # Get the image file from the request
        file = request.files['image']
        
        # Read the image using PIL
        image = Image.open(io.BytesIO(file.read()))
        
        # Ensure the image is in RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Define queries for object detection
        queries = [["a photo of a pokemon", "a photo of a human face", "a photo of a couch", "a photo of kids toys"]]

        # Process image with OWL-ViT
        inputs = od_processor(text=queries, images=image, return_tensors="pt", padding=True).to(device)
        outputs = od_model(**inputs)

        # Get detection results
        results = od_processor.post_process(outputs, torch.tensor([image.size[::-1]]).to(device))

        # Convert tensors to lists for JSON serialization
        results_serializable = {
            "boxes": [box.tolist() for box in results[0]['boxes']],
            "scores": results[0]['scores'].tolist(),
            "labels": results[0]['labels'].tolist(),
            "text": queries[0]  # Include the text queries in the response
        }

        # Add CORS headers to the response
        response = jsonify(results_serializable)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run the Flask app
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)
