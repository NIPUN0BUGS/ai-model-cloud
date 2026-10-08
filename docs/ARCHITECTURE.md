# Architecture

```
Internet ──443──> Caddy (TLS, security headers, SSE-safe proxy)
                    ├── /v1/*, /api/* ──> FastAPI backend ──┬─> PostgreSQL   (data net, internal-only)
                    └── everything else > Next.js frontend  ├─> Redis        (data net, internal-only)
                                                            └─> Ollama       (inference net, no published port)
```

## Networks
| Network | Members | Notes |
|---|---|---|
| edge | caddy, frontend, backend | Only Caddy publishes ports 80/443 |
| data (internal: true) | postgres, redis, backend | No outbound internet |
| inference | ollama, backend | Ollama needs egress to pull models; has no published port |

## Backend layers
- `api/` routers (auth, chat, models, keys, usage, admin, `/v1` gateway)
- `auth/` Argon2, session cookies, API-key hashing (HMAC-SHA256 + pepper), RBAC dependencies
- `services/` ollama client, model manager, rate limiter (Redis), usage accounting, server router, SSRF guard
- `models/` SQLAlchemy tables, `database/` engine/session, `core/` config

## Key decisions
- **Sessions**: random 256-bit token in HTTP-only, Secure, SameSite=Lax cookie; only its SHA-256 is stored.
- **API keys**: `amc_<random>`; only HMAC hash + display prefix stored; full key shown once.
- **Streaming**: SSE for playground; OpenAI-style `data:` chunks for `/v1/chat/completions`.
- **Rate limiting**: Redis fixed-window counters (login, per-user, per-key) + semaphore-style concurrency counters.
- **SSRF**: only super admins can register Ollama URLs; scheme allow-list, no redirects followed, resolved IPs checked.
- **LiteLLM**: deliberately NOT in the MVP stack. Our gateway talks to Ollama directly; adding LiteLLM later is a
  routing-layer swap, not a schema change.
- **Metrics honesty**: host CPU/RAM/disk come from `psutil` in the backend container (container view, not necessarily the
  Ollama host). GPU/Ollama-host metrics show "Unavailable" unless measured.
