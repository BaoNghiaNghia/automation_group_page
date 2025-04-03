# Use Python 3.12-slim as the base image
FROM python:3.12-slim

# Set environment variables to configure Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# Set the working directory to /app
WORKDIR /app

# Install necessary system dependencies for Chromium and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    # chromium \
    # chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chromium and chromedriver paths
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set proper permissions for the app
RUN chmod -R 755 /app

# Expose the app port
EXPOSE 9090

# Command to run the app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9090", "--reload"]
