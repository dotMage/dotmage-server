FROM python:3.13-slim

WORKDIR /srv
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/ src/
COPY main.py .

# Web admin static files (copy built dist here, or mount as volume)
RUN mkdir -p /app/static
ENV DOTMAGE_STATIC_DIR=/app/static

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
