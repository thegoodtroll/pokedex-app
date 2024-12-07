#!/bin/bash

# Build the Docker image
docker build -t flask-backend .

# Tag the image for Google Container Registry
docker tag flask-backend gcr.io/pokemonflaskapi/flask-backend

# Push the image to Google Container Registry
docker push gcr.io/pokemonflaskapi/flask-backend

# Deploy to Cloud Run
gcloud run deploy flask-backend \
  --image gcr.io/pokemonflaskapi/flask-backend \
  --platform managed \
  --region europe-west1 \
  --project pokemonflaskapi \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 50 \
  --cpu-boost \
  --execution-environment gen2
