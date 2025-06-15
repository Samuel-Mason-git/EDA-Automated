# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files into container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (waitress runs on 8000)
EXPOSE 8000

# Run app with waitress
CMD ["waitress-serve", "--port=8000", "--threads=4", "--channel-timeout=1800", "app:app"]
