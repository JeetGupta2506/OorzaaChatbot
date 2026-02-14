# Mitraa Chatbot – Deployment Guide

This guide covers deploying the **backend (FastAPI)** and **frontend (widget + admin)** for production. You use **Chroma Cloud** and **Admin upload** for the knowledge base, so no local vector DB or `knowledge/` folder is required on the server.

---

## 1. What You Need to Deploy

| Component | Description |
|-----------|-------------|
| **Backend** | FastAPI app (Python). Serves `/api/chat`, `/api/knowledge/upload`, etc. |
| **Frontend** | Static files: `chatbot-widget.js`, `chatbot-widget.css`, `admin.html`, `index.html`. The main site (e.g. oorzaayatra.com) will embed the widget and point it to your backend URL. |
| **Chroma Cloud** | Already set up; backend connects via env vars. |
| **OpenAI** | API key in env. |

---

## 2. Environment Variables (Backend)

Set these in your hosting platform (Railway, Render, etc.) or in a `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | **Yes** | Your OpenAI API key. |
| `CHROMA_USE_CLOUD` | Yes (for you) | Set to `true`. |
| `CHROMA_CLOUD_HOST` | Yes | Chroma Cloud host (e.g. `xxx.trychroma.com`). |
| `CHROMA_CLOUD_API_KEY` | Yes | Chroma Cloud API key. |
| `PORT` | Optional | Port the app listens on. Default `8000`. Railway/Render set this automatically. |

---

## 3. Deploy the Backend

### Option A: Railway (recommended for simplicity)

1. Sign up at [railway.app](https://railway.app).
2. **New Project** → **Deploy from GitHub** (connect your repo) or **Empty Project** and deploy with CLI.
3. If using GitHub: select the repo, set **Root Directory** to `backend` (or deploy the whole repo and set root to `backend`). Railway will detect Python and run `pip install -r requirements.txt` if you add a `nixpacks.toml` or use a Dockerfile.
4. Add a **Dockerfile** in `backend/` (see below) and Railway will build and run it. Or without Docker: set **Start Command** to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. In **Variables**, add:
   - `OPENAI_API_KEY`
   - `CHROMA_USE_CLOUD=true`
   - `CHROMA_CLOUD_HOST`
   - `CHROMA_CLOUD_API_KEY`
6. Deploy. Note the public URL (e.g. `https://your-app.railway.app`).

### Option B: Render

1. Sign up at [render.com](https://render.com).
2. **New** → **Web Service**. Connect the repo.
3. **Root Directory:** `backend`.
4. **Runtime:** Python 3.
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add **Environment Variables** (same as above).
8. Deploy and copy the service URL (e.g. `https://your-app.onrender.com`).

### Option C: Docker (any VPS or cloud)

1. Build and run from the **project root** (Dockerfile context includes `backend/`):

   ```bash
   docker build -t mitraa-backend -f backend/Dockerfile ./backend
   docker run -p 8000:8000 \
     -e OPENAI_API_KEY=sk-... \
     -e CHROMA_USE_CLOUD=true \
     -e CHROMA_CLOUD_HOST=xxx.trychroma.com \
     -e CHROMA_CLOUD_API_KEY=... \
     mitraa-backend
   ```

2. On a VPS, use a reverse proxy (nginx/Caddy) and HTTPS. Set `PORT=8000` or leave default.

---

## 4. Backend Dockerfile

A `backend/Dockerfile` is provided. It:

- Uses a Python image, installs dependencies, and runs `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- Expects `PORT` to be set by the platform (Railway/Render) or defaults to 8000.

Build from repo root:

```bash
docker build -f backend/Dockerfile -t mitraa-backend ./backend
```

---

## 5. Deploy the Frontend (Widget + Admin)

The frontend is static. You have two approaches:

### Option A: Same domain as backend (e.g. `api.oorzaayatra.com`)

- Serve the backend with a reverse proxy (e.g. nginx) that:
  - Proxies `/api/*` to the FastAPI app.
  - Serves static files for `/chatbot/*` (e.g. `chatbot-widget.js`, `chatbot-widget.css`) and `/admin` (e.g. `admin.html`).
- Then:
  - Widget: `apiUrl: 'https://api.oorzaayatra.com'`
  - Admin: open `https://api.oorzaayatra.com/admin`
  - Embed: point script/style and `apiUrl` to `https://api.oorzaayatra.com`

### Option B: Frontend on a different host (e.g. main website or CDN)

- Upload `chatbot-widget.js`, `chatbot-widget.css`, and (if needed) `admin.html` to your main site or a CDN.
- In the **embed snippet** on oorzaayatra.com (or any page), set:
  - Script and CSS URLs to where you host those files.
  - `apiUrl` to your **backend URL** (e.g. `https://your-app.railway.app` or `https://api.oorzaayatra.com`).

Example for embed on the main website:

```html
<div id="oorzaa-chatbot-widget"></div>
<link rel="stylesheet" href="https://oorzaayatra.com/chatbot/chatbot-widget.css">
<script src="https://oorzaayatra.com/chatbot/chatbot-widget.js"></script>
<script>
  OorzaaChatbot.init({
    apiUrl: 'https://your-backend-url.railway.app',  // your deployed backend
    position: 'bottom-right'
  });
</script>
```

---

## 6. Point Admin and Demo to Production API

- **Admin** (`admin.html`): Change the API base URL from `http://localhost:8000` to your deployed backend URL (e.g. `https://your-app.railway.app`). You can do this by:
  - Editing `admin.html` and replacing `const API_URL = 'http://localhost:8000'` with your backend URL, then deploying that file, or
  - Serving a version of admin that reads the API URL from a config or query param.
- **Demo** (`index.html`): Same idea – set `apiUrl` in `OorzaaChatbot.init({...})` to your backend URL before deploying.

CORS is already set to allow all origins (`allow_origins=["*"]`), so the widget on any domain can call your backend.

---

## 7. Checklist Before Go-Live

- [ ] Backend env: `OPENAI_API_KEY`, `CHROMA_USE_CLOUD`, `CHROMA_CLOUD_HOST`, `CHROMA_CLOUD_API_KEY` (and `PORT` if needed).
- [ ] Backend is reachable at a public HTTPS URL.
- [ ] Widget embed uses this URL in `apiUrl`.
- [ ] Admin page uses this URL so uploads go to the live API.
- [ ] Chroma Cloud has the intended knowledge base (you can upload/update via Admin after deploy).
- [ ] Optional: Restrict CORS to your domains instead of `*` (set `allow_origins` in `main.py` to a list of your frontend origins).

---

## 8. Optional: Restrict CORS

If you want to allow only your website:

1. In `backend/main.py`, replace:
   ```python
   allow_origins=["*"],
   ```
   with:
   ```python
   allow_origins=["https://oorzaayatra.com", "https://www.oorzaayatra.com"],
   ```
2. Add any other origins (e.g. admin subdomain) as needed.

---

## Summary

1. Deploy the **backend** (Railway, Render, or Docker) with the required env vars and Chroma Cloud.
2. Host the **widget assets** (and optionally admin) on your main site or same host as the API.
3. Set **apiUrl** (and Admin API URL) to your **deployed backend URL** everywhere.
4. Use **Admin** to upload/manage knowledge in Chroma Cloud; no server restart needed for content updates.
