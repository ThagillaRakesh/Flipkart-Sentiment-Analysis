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

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy project files
COPY . .

# Pre-download NLTK data so it's baked into the image
RUN python3 -c "\
import nltk; \
[nltk.download(p, quiet=True) for p in \
 ['stopwords','wordnet','omw-1.4','punkt','punkt_tab']]"

EXPOSE 5000

# gunicorn with long timeout for scraping requests
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "600", "--workers", "1", "app:app"]
