# Oorzaa Yatra Chatbot Backend

FastAPI backend for the Oorzaa Yatra spiritual travel chatbot with OpenAI LLM integration.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variable:
```bash
set OPENAI_API_KEY=your_api_key_here
```

4. Run the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `POST /api/chat` - Send message and get response
- `GET /api/health` - Health check
