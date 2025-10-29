# Dockerfile
FROM python:3.9-slim

# Set working directory to /app
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY hello_world.py .

# Expose port
EXPOSE 80

# Run command
CMD ["python", "hello_world.py"]