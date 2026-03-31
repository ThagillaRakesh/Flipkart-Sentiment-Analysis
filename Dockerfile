FROM python:3.11-slim

# Install Chromium + ChromeDriver (needed for Selenium scraping)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome binary path for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Ensure Python output is sent straight to logs (no buffering)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install Python dependencies (gunicorn is in requirements.txt — no need to repeat it)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Pre-download NLTK data so it's baked into the image (no network needed at runtime)
RUN python3 -c "\
import nltk; \
[nltk.download(p, quiet=True) for p in \
 ['stopwords','wordnet','omw-1.4','punkt','punkt_tab']]"

EXPOSE 5000

# gunicorn with long timeout for scraping requests
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "--workers", "1", "app:app"]
