# TrustCard Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Tesseract OCR and FFmpeg for video processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    postgresql-client \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    libtesseract-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy language model for NLP
RUN pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1.tar.gz

# Download NLTK data for text processing
RUN python -m nltk.downloader punkt stopwords averaged_perceptron_tagger

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
