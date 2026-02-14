# Mitraa Chatbot Backend - production image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY main.py .

# Default port (override with PORT env in Railway/Render)
ENV PORT=8000
EXPOSE 8000

# Run with PORT from environment so Railway/Render work
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
