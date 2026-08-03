# MSALGCM Dashboard

React + FastAPI dashboard for live experiment progress and interactive analysis.

## One-command dev (recommended)

From the **project root**:

```bash
pip install -e ".[web,viz]"
npm install          # installs concurrently (first time only)
npm run dev          # API hot-reload + React hot-reload
```

Or via the Python CLI wrapper (same thing):

```bash
optimize dev
```

Open **http://localhost:5173**

- **api** — FastAPI on port 8000 with `--reload`
- **web** — Vite dev server on port 5173 (proxies `/api` → 8000)

Press `Ctrl+C` once to stop both.

## Manual two-terminal setup

**Terminal 1:**
```bash
optimize serve --reload
```

**Terminal 2:**
```bash
cd web/frontend && npm run dev
```

## Production (single server)

```bash
npm run build:web
optimize serve --with-frontend
```

Open **http://127.0.0.1:8000**

## Features

- **Dashboard** — recent experiments and scalability studies
- **Experiment detail** — summary table, interactive convergence charts, PNG exports
- **Study detail** — scalability gap charts across problem sizes
- **Run experiment** — start jobs from example configs, live progress bar, partial results while running

## npm scripts (project root)

| Script | Description |
|--------|-------------|
| `npm run dev` | API + React dev servers (concurrently) |
| `npm run build:web` | Production frontend build |
| `npm run serve` | Build frontend + serve API with static UI |

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/dashboard` | Overview data |
| `GET /api/experiments` | List experiments |
| `GET /api/experiments/{id}` | Experiment detail |
| `GET /api/experiments/{id}/convergence/{run_id}` | Convergence series (JSON) |
| `GET /api/studies/{id}` | Study detail + scalability summary |
| `POST /api/jobs/run` | Start experiment or study in background |
| `GET /api/jobs/{id}` | Job progress |
