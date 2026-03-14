FROM python:3.11-slim
 
# Set working directory
WORKDIR /app
 
# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy source code
COPY . .
 
# Collect static files
RUN python manage.py collectstatic --noinput || true
 
# Expose port
EXPOSE 8000
 
# Run with gunicorn for production-style serving
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
