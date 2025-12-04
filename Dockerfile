# Use a slim Python base image
FROM python:3.11-slim

# Avoid Python writing .pyc files and buffering logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Make /app importable as a Python module root (so 'import app.*' works)
ENV PYTHONPATH="/app"

# Install system dependencies (optional but helpful for some packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker cache
COPY requirements.txt /app/

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the whole project
COPY . /app

# Expose the port we ACTUALLY use with Streamlit
EXPOSE 8000

# Final command: run Streamlit app on port 8000
ENTRYPOINT ["streamlit", "run", "app/dashboard.py", "--server.port=8000", "--server.address=0.0.0.0"]
