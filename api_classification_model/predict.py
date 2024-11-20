import os
from flask import Flask, request, jsonify
from PIL import Image
import torch
from transformers import ViTForImageClassification, ViTImageProcessor
import io

# Initialize Flask app
app = Flask(__name__)

# Load the classification model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
classification_model = ViTForImageClassification.from_pretrained("shorndrup/pokemon-classification-model").to(device)
feature_extractor = ViTImageProcessor.from_pretrained("shorndrup/pokemon-classification-model")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/classify', methods=['POST', 'OPTIONS'])
def classify():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    # Check if an image is present in the request
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

        # Process image and get prediction
        extracted = feature_extractor(images=image, return_tensors='pt').to(device)
        predicted_id = classification_model(**extracted).logits.argmax(-1).item()
        predicted_pokemon = classification_model.config.id2label[predicted_id]

        # Prepare the response
        result = {
            "predicted_pokemon": predicted_pokemon,
            "confidence": 1.0  # Add confidence score if needed
        }

        # Add CORS headers to the response
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run the Flask app
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)
