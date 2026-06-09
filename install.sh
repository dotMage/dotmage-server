#!/bin/bash
set -e

DIR="dotmage"
mkdir -p "$DIR"
cd "$DIR"

cat > docker-compose.yml << 'EOF'
version: "3.8"

services:
  server:
    image: ghcr.io/dotmage/dotmage-server:latest
    restart: unless-stopped
    environment:
      DOTMAGE_DB_URL: "sqlite:////data/dotmage.db"
      DOTMAGE_BOOTSTRAP_SECRET: ""
      DOTMAGE_TOKEN_TTL: "24h"
      DOTMAGE_REFRESH_TTL: "30d"
      DOTMAGE_LOG_LEVEL: "info"
    volumes:
      - dotmage-data:/data
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  dotmage-data:
EOF

# Detect docker compose command
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
elif docker-compose version >/dev/null 2>&1; then
    DC="docker-compose"
else
    echo "Error: docker compose not found" >&2
    exit 1
fi

echo "Pulling dotMage..."
$DC pull

echo "Starting dotMage..."
$DC up -d

echo ""
echo "==============================="
echo "  dotMage is running!"
echo "  http://$(hostname -f 2>/dev/null || echo localhost):8000"
echo "==============================="
echo ""
echo "Bootstrap secret (save it!):"
sleep 3
$DC logs server 2>&1 | grep -i "bootstrap secret" || echo "Run: $DC logs server | grep 'bootstrap secret'"
echo ""
echo "Next: install dmage CLI from https://github.com/dotMage/dotmage-cli/releases"
