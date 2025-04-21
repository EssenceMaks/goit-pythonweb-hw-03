FROM python:3.11-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create and set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN adduser -D appuser && \
    chown -R appuser:appuser /app

# Create storage directory with proper permissions
RUN mkdir -p /app/storage && \
    chown -R appuser:appuser /app/storage

# Copy application files
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3003

# Run application with optimizations
CMD ["python3", "-O", "main.py"]