# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for GeoPandas and Shapely
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libspatialindex-dev \
    gdal-bin \
    python3-dev \
    python3-pip \
    libgdal-dev \
    libproj-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL and PROJ paths for compatibility
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    Flask \
    requests \
    python-dotenv \
    geopandas \
    shapely \
    flask-httpauth \
    werkzeug

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
