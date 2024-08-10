# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code to the working directory
COPY . /app

# Install required packages
RUN pip install --no-cache-dir telebot python-binance

# Expose the port your app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]