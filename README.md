# Buildra — AI Software Factory Platform

Submit a product requirement in natural language. Buildra clarifies, architects, generates tickets, and executes tasks via OpenDevin to deliver a working application.

## Quick Start

```bash
cp .env.example .env
# Edit .env with your ENCRYPTION_KEY and LLM settings

docker compose up
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **OpenDevin**: http://localhost:3001

## Flow

1. Go to **Settings** → configure your LLM (endpoint, API key, model)
2. Click **New Project** → enter your product requirement
3. Answer clarification questions
4. Review the generated architecture → click **Approve**
5. Tickets are generated → click **Execute**
6. Watch live logs as OpenDevin builds your project
7. Download the finished project

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
/frontend   Next.js 14 + Tailwind + shadcn/ui
/backend    FastAPI + SQLite
/tickets    JSON ticket files per project
/docs       Generated architecture documents
/workspace  OpenDevin working directory
```
