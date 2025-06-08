#!/bin/bash

# Run like:
#./deploy_smart_meter.sh \
#  --name smart-meter-mqtt \
#  --version v1.2.3 \
#  --nuc-host 192.168.2.64 \
#  --nuc-user nucadmin


# Default values
IMAGE_NAME="smart-meter-mqtt"
VERSION="v1.0.0"

# Parse named arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --name) IMAGE_NAME="$2"; shift ;;
    --version) VERSION="$2"; shift ;;
    --nuc-host) NUC_HOST="$2"; shift ;;
    --nuc-user) NUC_USER="$2"; shift ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

# Derived variables
GHCR="ghcr.io/mauriciosalazare/${IMAGE_NAME}:${VERSION}"
NUC_ENV_PATH="/home/${NUC_USER:-nucadmin}/smart-meter/.env"
NUC_HOST="${NUC_HOST:-192.168.2.64}"
NUC_USER="${NUC_USER:-nucadmin}"

# Build and push Docker image
echo "Building and pushing $GHCR..."
docker buildx build --platform linux/amd64 -t $GHCR --push .

# Create remote dir
echo "Ensuring remote path exists..."
ssh ${NUC_USER}@${NUC_HOST} "mkdir -p $(dirname $NUC_ENV_PATH)"

# Copy .env
echo "Copying .env to ${NUC_HOST}..."
scp .env ${NUC_USER}@${NUC_HOST}:${NUC_ENV_PATH}

echo "Done."
