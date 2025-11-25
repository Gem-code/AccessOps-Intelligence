# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create .streamlit directory and config
RUN mkdir -p ~/.streamlit && \
    echo "\
[server]\n\
port = 8080\n\
address = 0.0.0.0\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
\n\
[theme]\n\
primaryColor = '#ff4b4b'\n\
backgroundColor = '#0e1117'\n\
secondaryBackgroundColor = '#1a1d29'\n\
textColor = '#ffffff'\n\
font = 'sans serif'\n\
" > ~/.streamlit/config.toml

# Expose port for Cloud Run
EXPOSE 8080

# Health check endpoint
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
