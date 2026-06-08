#!/bin/bash
set -e

# Clone or update web admin source before Docker build
WEB_DIR="web"

if [ -d "$WEB_DIR/.git" ]; then
    echo "Updating dotmage-web..."
    git -C "$WEB_DIR" pull --ff-only
else
    echo "Cloning dotmage-web..."
    rm -rf "$WEB_DIR"
    git clone --depth 1 git@github.com:dotMage/dotmage-web.git "$WEB_DIR"
fi

echo "Building Docker image..."
docker compose build
echo "Done. Run: docker compose up -d"
