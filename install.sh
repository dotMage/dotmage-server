#!/bin/bash
set -e

PORT_API=9470
PORT_WEB=9471
DIR="dotmage"

echo ""
echo "  \033[36m·  dotMage installer  ·\033[0m"
echo ""

mkdir -p "$DIR"
cd "$DIR"

cat > docker-compose.yml << EOF
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
      - "${PORT_API}:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3

  web:
    image: ghcr.io/dotmage/dotmage-server:latest
    restart: unless-stopped
    entrypoint: ["python", "-m", "http.server", "80", "--directory", "/app/static"]
    ports:
      - "${PORT_WEB}:80"

volumes:
  dotmage-data:
EOF

# Detect docker compose command
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
elif docker-compose version >/dev/null 2>&1; then
    DC="docker-compose"
else
    echo "  \033[31mError:\033[0m docker compose not found" >&2
    exit 1
fi

echo "  Pulling images..."
$DC pull -q 2>/dev/null || $DC pull

echo "  Starting services..."
$DC up -d 2>/dev/null

# Detect public IP
PUBLIC_IP=$(curl -s --max-time 3 ifconfig.me 2>/dev/null \
         || curl -s --max-time 3 icanhazip.com 2>/dev/null \
         || hostname -I 2>/dev/null | awk '{print $1}' \
         || echo "localhost")

echo ""
echo "  \033[32m✓ dotMage is running!\033[0m"
echo ""
echo "  ┌────────────────────────────────────────────────────┐"
echo "  │                                                    │"
printf "  │  \033[1mAPI\033[0m           http://%-30s│\n" "${PUBLIC_IP}:${PORT_API}"
printf "  │  \033[1mAdmin Panel\033[0m   http://%-30s│\n" "${PUBLIC_IP}:${PORT_WEB}"
echo "  │                                                    │"
echo "  └────────────────────────────────────────────────────┘"

sleep 3
SECRET=$($DC logs server 2>&1 | grep "bootstrap secret" | sed 's/.*secret: //' | tail -1)

echo ""
if [ -n "$SECRET" ]; then
    echo "  \033[33m🔑 Bootstrap secret (save it!):\033[0m"
    echo ""
    echo "     \033[1m${SECRET}\033[0m"
else
    echo "  \033[90mBootstrap secret not ready yet. Run:\033[0m"
    echo "  cd $DIR && $DC logs server | grep 'bootstrap secret'"
fi

echo ""
echo "  \033[90m── Next steps ──────────────────────────────────────\033[0m"
echo ""
echo "  1. Download CLI:  \033[4mhttps://github.com/dotMage/dotmage-cli/releases\033[0m"
echo "  2. Authenticate:  dmage auth --server http://${PUBLIC_IP}:${PORT_API}"
echo "  3. Push secrets:  cd your-project && dmage init myapp"
echo "  4. Admin panel:   \033[4mhttp://${PUBLIC_IP}:${PORT_WEB}\033[0m"
echo ""
