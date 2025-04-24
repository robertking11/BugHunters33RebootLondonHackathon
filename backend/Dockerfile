# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "main_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]