# TyphoonLink — Production & Hackathon Deployment Guide

This guide covers all deployment strategies for **TyphoonLink**, from a single-command All-in-One deployment (recommended for hackathons and demos) to separate decoupled Cloud deployments (Vercel/Netlify + Render/Railway).

---

## ⚡ Option 1: Unified All-in-One Deployment (Recommended)

In this approach, the FastAPI backend serves both the REST API (`/api/...`) and the PWA frontend (`/*`). 
- **Benefits**: Zero CORS headaches, single domain, automatic HTTPS, perfect for Render/Railway/Fly.io.

### Step 1: Mount Static Files in FastAPI
In `server/app/main.py`, mount the `stitch_typhoon_link_sos` directory using FastAPI's built-in static handler:

```python
from fastapi.staticfiles import StaticFiles
import os

# Path to frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../stitch_typhoon_link_sos"))

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
```

### Step 2: Deploy to Render.com (Free Tier)
1. Push your repository to GitHub.
2. Sign in to [Render.com](https://render.com) and click **New +** $\rightarrow$ **Web Service**.
3. Connect your repository `TYPHOON-LINK1`.
4. Configure service settings:
   - **Name**: `typhoon-link`
   - **Root Directory**: `server`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   - `JWT_SECRET`: *(Generate a secure random string)*
   - `ALLOWED_ORIGINS`: `*`
   - `DATABASE_URL`: `sqlite:///./database/typhoon_server.db`
6. Click **Deploy Web Service**.

Your app is live with HTTPS (e.g., `https://typhoon-link.onrender.com/citizen_offline_sos_dispatcher_simplified/code.html`).

---

## 🌐 Option 2: Decoupled Cloud Deployment

### Part A: Deploy Backend (Render / Railway / Koyeb)

#### Deploying on Railway:
1. Log in to [Railway.app](https://railway.app).
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select `TYPHOON-LINK1` and specify root directory `server`.
4. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. In **Variables**, add:
   - `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app,*`
   - `JWT_SECRET`: `your-production-secret-here`
6. Railway will assign an HTTPS URL: `https://typhoon-backend-production.up.railway.app`.

---

### Part B: Deploy Frontend (Vercel / GitHub Pages / Netlify)

Because the frontend is pure HTML5, CSS3, and JavaScript, it can be hosted on any static edge CDN.

#### Deploying on Vercel:
1. Go to [Vercel.com](https://vercel.com) and click **Add New Project**.
2. Select repository `TYPHOON-LINK1`.
3. Set **Root Directory** to `stitch_typhoon_link_sos`.
4. Leave build settings as default (No build command needed).
5. Click **Deploy**.
6. Vercel provides instant HTTPS (required for Service Workers and PWA offline storage).

#### Deploying on GitHub Pages:
1. In your GitHub repository, go to **Settings** $\rightarrow$ **Pages**.
2. Under **Build and deployment**, set Source to **Deploy from a branch**.
3. Select branch `main` and folder `/stitch_typhoon_link_sos` (or root).
4. Click **Save**.

---

## 🐳 Option 3: Docker Deployment

Create a `Dockerfile` inside `typhoon-link/`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and frontend
COPY server/ ./server/
COPY stitch_typhoon_link_sos/ ./stitch_typhoon_link_sos/

WORKDIR /app/server

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t typhoon-link .
docker run -p 8000:8000 typhoon-link
```

---

## 🔒 Production Security Checklist

Before deploying to live coastal disaster response networks:

1. **Environment Secrets**: Ensure `JWT_SECRET` is set to a cryptographically strong 256-bit string. Never commit `.env` to GitHub.
2. **CORS Restrictions**: Replace `ALLOWED_ORIGINS=*` with your exact frontend domain (e.g. `https://typhoon-link.vercel.app`).
3. **Database Persistence**: On cloud containers like Render or Railway, container filesystems are ephemeral. Attach a **Persistent Disk Volume** to `/database` to preserve SQLite records across restarts, or switch to PostgreSQL by changing `DATABASE_URL`.
4. **HTTPS Enforcement**: Service Workers and Geolocation APIs require HTTPS to operate securely in modern browsers.
