from flask import Flask, jsonify, request, send_file
from flask_cors import CORS  # Add this import
from PIL import Image, ImageDraw
import io
import torch
from transformers import OwlViTProcessor, OwlViTForObjectDetection, ViTForImageClassification, ViTImageProcessor
import base64
import os

app = Flask(__name__)

CORS(app)

# Set the base directory to the parent of backend_env
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Load the OWL-ViT model and processor
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
od_processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
od_model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32").to(device)

# Load the classification model
#classification_model = ViTForImageClassification.from_pretrained(os.path.join(base_dir, "Classification_model")).to(device)
#feature_extractor = ViTImageProcessor.from_pretrained(os.path.join(base_dir, "Classification_model"))

classification_model = ViTForImageClassification.from_pretrained("shorndrup/pokemon-classification-model").to(device)
feature_extractor = ViTImageProcessor.from_pretrained("shorndrup/pokemon-classification-model")


# Define valid Pokémon categories and image folder
valid_categories = [category.lower() for category in classification_model.config.id2label.values()]
pokemon_image_folder = os.path.join(base_dir, 'images')


@app.route("/")  # This route handles requests to '/'
def home():
    return "Flask App is initialized properly!"


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
    # Define your queries
    queries = [["a photo of a pokemon", "a photo of a human face", "a photo of a couch", "a photo of kids toys"]]

    # Use object detection model on image
    inputs = od_processor(text=queries, images=image, return_tensors="pt", padding=True).to(device)
    outputs = od_model(**inputs)

    # Process outputs to get bounding boxes and scores
    results = od_processor.post_process(outputs, torch.tensor([image.size[::-1]]).to(device))

    i = 0  # Retrieve predictions for the first image for the corresponding text queries
    text = queries[i]
    boxes, scores, labels = results[i]["boxes"], results[i]["scores"], results[i]["labels"]

    # Initialize variables to track the best detection
    score_threshold = 0.01  # set the threshold for the predicted boxes
    best_box = None
    highest_score = 0

    # Iterate through each detected object and save the cropped region for "a photo of a pokemon" with the highest score
    for box, score, label in zip(boxes, scores, labels):
        if score >= score_threshold:
            # Convert box coordinates to integers
            box = [int(round(i)) for i in box.tolist()]

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
                # Convert box coordinates to integers
                box = [int(round(i)) for i in box.tolist()]

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


def classification(image_cropped):
    extracted = feature_extractor(images=image_cropped, return_tensors='pt').to(device)
    predicted_id = classification_model(**extracted).logits.argmax(-1).item()
    predicted_pokemon = classification_model.config.id2label[predicted_id]
    return predicted_pokemon


def get_pokemon_image(predicted_pokemon):
    # Normalize predicted Pokémon name
    predicted_pokemon = predicted_pokemon.lower().replace(" ", "-")  # Replace spaces with hyphens
    # Construct the image path
    image_path = os.path.join(pokemon_image_folder, f"{predicted_pokemon}.png")
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    else:
        print(f"Image not found for: {predicted_pokemon}")
        return None


if __name__ == '__main__':
    app.run(debug=True)
