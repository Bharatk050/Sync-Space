# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /sync_space

# Copy requirement files first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create output folder with proper permissions
RUN mkdir -p /sync_space/output && \
    chmod -R 777 /sync_space/output && \
    chown -R appuser:appuser /sync_space/output

# (Optional) Create a non-root user safely
RUN useradd -m appuser || true

# Set ownership after user creation
RUN chown -R appuser:appuser /sync_space

# Switch to non-root user
USER appuser

# Copy the rest of the code
COPY . .

# Expose ports for both FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501

# Default command (can be overridden by docker-compose)
CMD ["bash"]
