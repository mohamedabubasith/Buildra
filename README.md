# Buildra — AI Software Factory Platform

Submit a product requirement in natural language. Buildra clarifies, architects, generates tickets, and executes tasks via OpenDevin to deliver a working application.

---

## Deploy to the Internet (Netlify + Render) — 5 minutes

### 1 — Deploy backend to Render (free)

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Connect your GitHub repo (`mohamedabubasith/Buildra`)
3. Render will auto-detect `render.yaml` and fill everything in
4. Click **Create Web Service**
5. Note your backend URL: `https://buildra-api.onrender.com` (or similar)

### 2 — Deploy frontend to Netlify (free)

```bash
# On your own machine:
npm install -g netlify-cli
git clone https://github.com/mohamedabubasith/Buildra
cd Buildra
netlify deploy --build --prod
```

Or use Netlify UI:
1. Go to [app.netlify.com](https://app.netlify.com) → **Add new site** → **Import from Git**
2. Connect `mohamedabubasith/Buildra`
3. Netlify reads `netlify.toml` automatically — just click **Deploy**
4. Set environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL

---

## Local Development

```bash
cp .env.example .env
# Edit .env — set ENCRYPTION_KEY:
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

## Docker (production)

```bash
docker compose up
```

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **OpenDevin**: http://localhost:3001

---

## How it works

1. **Settings** → configure your LLM (API key, model, endpoint)
2. **New Project** → describe your product in plain English
3. Answer AI clarification questions
4. Review the generated architecture → **Approve**
5. Tickets are generated automatically
6. Click **Execute** → OpenDevin builds the project task by task
7. Watch live logs, then download your finished project

## Project Structure

```
/frontend      Next.js 14 + Tailwind + shadcn/ui
/backend       FastAPI + SQLite
/tickets       JSON ticket files per project
/docs          Generated architecture docs
/workspace     OpenDevin working directory
netlify.toml   One-click Netlify deploy config
render.yaml    One-click Render deploy config
```
