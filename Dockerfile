# Use official Python image
FROM python:3.10-slim

# keep Python output unbuffered (helpful for logs)
ENV PYTHONUNBUFFERED=1

# create a non-root user and group (run as root by default in build)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# set working directory
WORKDIR /sync_space

# copy only requirements first to use Docker layer caching
COPY requirements.txt .

# install dependencies as root (so caching works)
RUN pip install --no-cache-dir -r requirements.txt

# create output dir and set permissions (do this while still root)
RUN mkdir -p /sync_space/output \
    && chmod 0777 /sync_space/output \
    && chown -R appuser:appuser /sync_space/output

# copy the rest of the repo and set ownership to appuser
# --chown avoids an extra chown layer and ensures files are owned correctly
COPY --chown=appuser:appuser . .

# switch to non-root user for runtime
USER appuser

# expose ports your app uses (adjust if needed)
EXPOSE 8000
EXPOSE 8501

# default command (adjust as needed; example leaves you in bash)
CMD ["bash"]
