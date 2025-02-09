# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV MODULE_NAME=src.main
ENV VARIABLE_NAME=app
ENV PORT=8001

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"] 