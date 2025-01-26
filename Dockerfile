FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "receiver:app", "--host", "0.0.0.0", "--port", "8000"] 