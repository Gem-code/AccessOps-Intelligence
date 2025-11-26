FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for some Google / PDF libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy engine + Streamlit UI
COPY accessops_engine.py .
COPY app.py .

# Cloud Run convention: listen on $PORT (default 8080)
ENV PORT=8080 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8080

# Launch Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
