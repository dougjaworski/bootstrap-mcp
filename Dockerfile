# Bootstrap MCP Server Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port 8001
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV MCP_PORT=8001
ENV MCP_HOST=0.0.0.0

# Run the server using fastmcp
CMD ["fastmcp", "run", "run_server.py:mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "8001"]
