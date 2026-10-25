FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for container healthcheck and git + openssh-client for GitHub Pages push
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Configure git safe directory and identity
RUN git config --global --add safe.directory /app \
    && git config --global --add safe.directory '*' \
    && git config --global user.name "Joshua Lang" \
    && git config --global user.email "joshua.r.lang@gmail.com"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and assets
COPY app.py main.py db.py export_records.py sync.sh index.html records.json Icon.png ./
COPY .streamlit ./.streamlit
COPY static ./static
COPY times ./times

# Create persistent data and times directory mount points
RUN mkdir -p /app/data /app/times

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck to monitor app status
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start Streamlit bound to all interfaces
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
