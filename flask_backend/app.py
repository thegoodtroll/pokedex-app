from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageDraw
import io
import base64
import os
import requests

app = Flask(__name__, static_folder='../pokedex-gui/build', static_url_path='/')

# Configure CORS for production
CORS(app, resources={
    r"/upload-image": {"origins": "https://pokedex-1hlc.onrender.com"},  # Adjust this to specific domains in production
    r"/api/*": {"origins": "https://pokedex-1hlc.onrender.com"}
})

# Set the base directory to the parent of backend_env
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Cloud Run API endpoints
OWLVIT_API = "https://owl-vit-api-150344248755.europe-west1.run.app"
CLASSIFICATION_API = "https://pokemon-classification-api-150344248755.europe-west1.run.app"

# GitHub raw content URL for Pokemon images
GITHUB_RAW_URL = "https://raw.githubusercontent.com/thegoodtroll/pokedex-app/master/images"

# Serve React App's static files
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

# Serve React App's static files for all routes
@app.route('/<path:path>')
def serve_path(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health():
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
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    # Ensure image is in RGB mode before saving as JPEG
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    # Prepare the files for the request
    files = {
        'image': ('image.jpg', img_byte_arr, 'image/jpeg')
    }

    try:
        # Make request to Cloud Run API
        response = requests.post(f"{OWLVIT_API}/detect", files=files)
        
        if response.status_code == 200:
            results = response.json()
            boxes = results.get("boxes", [])
            scores = results.get("scores", [])
            labels = results.get("labels", [])
            text = results.get("text", [])

            # Initialize variables to track the best detection
            score_threshold = 0.01  # set the threshold for the predicted boxes
            best_box = None
            highest_score = 0

            # Iterate through each detected object and save the cropped region for "a photo of a pokemon" with the highest score
            for box, score, label in zip(boxes, scores, labels):
                if score >= score_threshold:
                    if text[label] == "a photo of a pokemon":
                        if score > highest_score:
                            highest_score = score
                            best_box = box

            if best_box is not None:
                print("Pokemon detected!")

                # The cropped image for classification
                cropped_image = image.crop(best_box)

                # Draw rectangle
                draw = ImageDraw.Draw(image)
                draw.rectangle(best_box, outline="red", width=3)

                return {"detected": True, "image": image}, cropped_image

            else:
                # Initialize variables to track the highest probability and its corresponding box
                score_threshold = 0.01  # set the threshold for the predicted boxes
                highest_score = 0
                best_box = None

                for box, score, label in zip(boxes, scores, labels):
                    if score >= score_threshold:
                        if score > highest_score:
                            highest_score = score
                            best_box = box

                if best_box is not None:
                    print("No Pokemon detected!")
                    draw = ImageDraw.Draw(image)
                    draw.rectangle(best_box, outline="black", width=3)
                    return {"detected": False, "image": image}, None

                else:
                    print("No boxes detected on image!")
                    return {"detected": False, "image": image}, None
        else:
            print(f"API request failed with status code: {response.status_code}")
            return {"detected": False, "image": image}, None

    except Exception as e:
        print(f"Error calling Cloud Run API: {str(e)}")
        return {"detected": False, "image": image}, None

def classification(image_cropped):
    try:
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image_cropped.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        # Prepare the files for the request
        files = {
            'image': ('image.jpg', img_byte_arr, 'image/jpeg')
        }

        # Make request to Classification API
        response = requests.post(f"{CLASSIFICATION_API}/classify", files=files)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("predicted_pokemon")
        else:
            print(f"Classification API request failed with status code: {response.status_code}")
            return "Unknown Pokemon"

    except Exception as e:
        print(f"Error calling Classification API: {str(e)}")
        return "Unknown Pokemon"

def get_pokemon_image(predicted_pokemon):
    try:
        # Normalize predicted Pokémon name
        predicted_pokemon = predicted_pokemon.lower().replace(" ", "-")

        # Construct the GitHub raw URL for the image
        image_url = f"{GITHUB_RAW_URL}/{predicted_pokemon}.png"

        # Fetch the image from GitHub
        response = requests.get(image_url)

        # Check if the request was successful
        if response.status_code == 200:
            # Convert the image data to base64
            return base64.b64encode(response.content).decode("utf-8")
        else:
            print(f"Failed to fetch image for {predicted_pokemon}. Status code: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error fetching image for {predicted_pokemon}: {str(e)}")
        return None

if __name__ == '__main__':
    # In production you might want to use a production WSGI server
    # For development:
    app.run(debug=False, host='0.0.0.0', port=5000)
