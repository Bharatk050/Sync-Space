# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirement files first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create an output folder and fix permissions
RUN mkdir -p /app/output \
    && chmod -R 777 /app/output

# (Optional) Create a non-root user safely
RUN useradd -m appuser || true

# Set ownership after user creation
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy the rest of the code
COPY . .

# Expose ports for both FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501

# Default command (can be overridden by docker-compose)
CMD ["bash"]
