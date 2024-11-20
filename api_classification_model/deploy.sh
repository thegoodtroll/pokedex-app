#!/bin/bash

# Exit on any error
set -e

# Configuration
PROJECT_ID="150344248755"  # Project ID for pokemonflaskapi
REGION="europe-west1"
SERVICE_NAME="pokemon-classification-api"

# Build the container image
echo "Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2

echo "Deployment complete!"
echo "Make sure to update the CLASSIFICATION_API URL in app.py with the new Cloud Run endpoint."
