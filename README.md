# Oorzaa Yatra Chatbot

AI-powered chatbot for the Oorzaa Yatra spiritual travel platform, built with FastAPI and OpenAI.

## 🚀 Quick Start

### 1. Set up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
set OPENAI_API_KEY=your_key_here  # Windows

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test Frontend

Open `frontend/index.html` in your browser (or use a local server).

## 📁 Project Structure

```
OorzaChatbot/
├── backend/
│   ├── main.py           # FastAPI app with Gemini integration
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment template
├── frontend/
│   ├── index.html        # Demo page
│   ├── chatbot-widget.css
│   ├── chatbot-widget.js
│   └── embed-snippet.html
└── README.md
```

## ✨ Features

- 🙏 Spiritual travel assistant persona
- 📋 Answers about yatras, pricing, policies
- 🔗 Deep linking to registration/contact pages
- 👤 Human handoff after 3 failed attempts
- 📱 Mobile responsive design
- 💬 Suggested questions for quick access

## 🔧 Configuration

Set `OPENAI_API_KEY` environment variable with your OpenAI API key (from https://platform.openai.com/api-keys).

## 📞 Support

For questions, contact: oorzaayatra@m2t.ai
