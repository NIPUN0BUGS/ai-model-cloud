# AI Model Cloud

FastAPI-based model hosting control plane. The Docker Compose stack runs the full local platform with PostgreSQL, Redis, Ollama, and Caddy. The Vercel deployment exposes the FastAPI web server and expects infrastructure services to be provided externally.

## Local Docker Run

1. Copy `.env.example` to `.env`.
2. Replace every `CHANGE_ME` value.
3. Start the stack:

```bash
docker compose up --build
```

## Vercel Deployment

This repository includes:

- `api/index.py` as the Vercel Python entrypoint.
- `vercel.json` to route all requests to FastAPI.
- root `requirements.txt` that installs the backend dependencies.

Configure these Vercel environment variables before using production endpoints:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `API_KEY_PEPPER`
- `CORS_ORIGINS`
- `DEFAULT_OLLAMA_URL`

Use hosted services for PostgreSQL and Redis, and point `DEFAULT_OLLAMA_URL` to a reachable model runtime. Vercel does not run the Docker Compose services or GPU/Ollama containers.

## Health Check

```bash
GET /healthz
```
