# Stage 1: Build web admin
FROM node:22-slim AS web-builder
WORKDIR /web
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/dotMage/dotmage-web.git .
RUN npm ci && npm run build

# Stage 2: Server
FROM python:3.13-slim
WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY main.py .

# Copy built web admin
COPY --from=web-builder /web/dist /app/static
ENV DOTMAGE_STATIC_DIR=/app/static

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
