from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from PIL import Image, ImageDraw, ExifTags
import io
import base64
import os
import requests
import torch
from dotenv import load_dotenv
from pokemon_description import PokemonDescriptionService

# Load environment variables from .env file
load_dotenv()
from transformers import OwlViTProcessor, OwlViTForObjectDetection, ViTForImageClassification, ViTImageProcessor

app = Flask(__name__)
description_service = PokemonDescriptionService()

# Configure CORS for production
CORS(app, resources={
    r"/upload-image": {"origins": ["https://pokedex-1hlc.onrender.com", "http://localhost:3000"]},
    r"/api/*": {"origins": ["https://pokedex-1hlc.onrender.com", "http://localhost:3000"]},
    r"/health-check": {"origins": ["https://pokedex-1hlc.onrender.com", "http://localhost:3000"]},
    r"/get-pokemon-description": {"origins": ["https://pokedex-1hlc.onrender.com", "http://localhost:3000"]},
    r"/text-to-speech": {"origins": ["https://pokedex-1hlc.onrender.com", "http://localhost:3000"]}
})

# Cloud Storage URL for Pokemon images
CLOUD_STORAGE_URL = "https://storage.googleapis.com/pokemonflaskapi-images"

# Initialize ML models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize OWL-ViT model
od_model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32").to(device)
od_processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")

# Initialize Classification model
classification_model = ViTForImageClassification.from_pretrained("shorndrup/pokemon-classification-model").to(device)
feature_extractor = ViTImageProcessor.from_pretrained("shorndrup/pokemon-classification-model")

def fix_image_rotation(image):
    try:
        # Get EXIF data
        exif = image._getexif()
        if exif is None:
            return image

        # Find the orientation tag
        orientation_key = None
        for key in ExifTags.TAGS.keys():
            if ExifTags.TAGS[key] == 'Orientation':
                orientation_key = key
                break

        if orientation_key is None or orientation_key not in exif:
            return image

        # Apply the rotation based on EXIF orientation
        orientation = exif[orientation_key]
        if orientation == 3:
            return image.rotate(180, expand=True)
        elif orientation == 6:
            return image.rotate(270, expand=True)
        elif orientation == 8:
            return image.rotate(90, expand=True)
        
    except (AttributeError, KeyError, IndexError):
        # If there's any error processing EXIF data, return original image
        pass
    
    return image

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/health-check')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/upload-image', methods=['POST'])
def upload_image():
    # Check if an image is present in the request
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    # Read the image file from the request
    image_file = request.files['image']

    # Open the image using PIL directly from memory
    image = Image.open(io.BytesIO(image_file.read()))
    
    # Fix image rotation based on EXIF data
    image = fix_image_rotation(image)

    # Run object detection
    detection_results, cropped_image = object_detection(image)

    # Convert the modified image to a BytesIO object
    buffered = io.BytesIO()
    detection_results["image"].save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # If a Pokemon was detected
    if detection_results["detected"]:
        # Get the predicted Pokemon name
        predicted_pokemon = classification(cropped_image)
        print(f"Predicted Pokemon: {predicted_pokemon}")

        # Get the corresponding Pokemon image
        pokemon_image = get_pokemon_image(predicted_pokemon)
        print(f"Pokemon image found: {'Yes' if pokemon_image else 'No'}")

        return jsonify({
            "image": img_str,
            "detected": True,
            "predicted_pokemon": predicted_pokemon,
            "pokemon_image": pokemon_image
        })
    else:
        return jsonify({
            "image": img_str,
            "detected": False,
            "predicted_pokemon": "No Pokémon detected",
            "pokemon_image": None
        })

def object_detection(image):
    try:
        # Ensure image is in RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Define queries for object detection
        queries = [["a photo of a pokemon", "a photo of a human face", "a photo of a couch", "a photo of kids toys"]]

        # Process image with OWL-ViT
        inputs = od_processor(text=queries, images=image, return_tensors="pt", padding=True).to(device)
        outputs = od_model(**inputs)

        # Get detection results
        results = od_processor.post_process(outputs, torch.tensor([image.size[::-1]]).to(device))

        # Initialize variables to track the best detection
        score_threshold = 0.01
        best_box = None
        highest_score = 0

        boxes = results[0]['boxes']
        scores = results[0]['scores']
        labels = results[0]['labels']

        # Find the best pokemon detection
        for box, score, label in zip(boxes, scores, labels):
            if score >= score_threshold:
                if queries[0][label] == "a photo of a pokemon":
                    if score > highest_score:
                        highest_score = score
                        best_box = box.tolist()

        if best_box is not None:
            print("Pokemon detected!")

            # The cropped image for classification
            cropped_image = image.crop(best_box)

            # Draw rectangle
            draw = ImageDraw.Draw(image)
            draw.rectangle(best_box, outline="red", width=3)

            return {"detected": True, "image": image}, cropped_image

        else:
            # Initialize variables for any detection
            highest_score = 0
            best_box = None

            for box, score, label in zip(boxes, scores, labels):
                if score >= score_threshold:
                    if score > highest_score:
                        highest_score = score
                        best_box = box.tolist()

            if best_box is not None:
                print("No Pokemon detected!")
                draw = ImageDraw.Draw(image)
                draw.rectangle(best_box, outline="black", width=3)
                return {"detected": False, "image": image}, None

            else:
                print("No boxes detected on image!")
                return {"detected": False, "image": image}, None

    except Exception as e:
        print(f"Error in object detection: {str(e)}")
        return {"detected": False, "image": image}, None

def classification(image_cropped):
    try:
        # Ensure the image is in RGB mode
        if image_cropped.mode != 'RGB':
            image_cropped = image_cropped.convert('RGB')

        # Process image and get prediction
        extracted = feature_extractor(images=image_cropped, return_tensors='pt').to(device)
        predicted_id = classification_model(**extracted).logits.argmax(-1).item()
        predicted_pokemon = classification_model.config.id2label[predicted_id]

        return predicted_pokemon

    except Exception as e:
        print(f"Error in classification: {str(e)}")
        return "Unknown Pokemon"

def get_pokemon_image(predicted_pokemon):
    try:
        # Normalize predicted Pokémon name
        predicted_pokemon = predicted_pokemon.lower().replace(" ", "-")
        
        # Construct the Cloud Storage URL for the image
        image_url = f"{CLOUD_STORAGE_URL}/{predicted_pokemon}.png"
        
        # Fetch the image from Cloud Storage
        response = requests.get(image_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Convert the image data to base64
            return base64.b64encode(response.content).decode("utf-8")
        else:
            print(f"Failed to fetch image for {predicted_pokemon}. Status code: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error getting image for {predicted_pokemon}: {str(e)}")
        return None

@app.route('/get-pokemon-description', methods=['POST'])
def get_pokemon_description():
    data = request.get_json()
    if not data or 'pokemon_name' not in data:
        return jsonify({"error": "No pokemon_name provided"}), 400
        
    pokemon_name = data['pokemon_name']
    description = description_service.get_pokemon_description(pokemon_name)
    
    if description:
        return jsonify({"description": description})
    else:
        return jsonify({"error": "Failed to get description"}), 500

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
        
    audio_data = description_service.get_audio_stream(data['text'])
    
    if audio_data:
        return Response(audio_data, mimetype='audio/mpeg')
    else:
        return jsonify({"error": "Failed to generate audio"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
