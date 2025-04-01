# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Celery
ENV CELERY_APP=celery_config.app
ENV CELERY_BROKER=redis://redis:6379/0

# Set the default command to run Celery worker and Beat
CMD ["celery", "-A", "celery_config.app", "worker", "--loglevel=info"]