# Deploying on AWS

Two services + one database. No Railway, no Vercel.

```
                         ┌─────────────────────────┐
   browser ───────────▶  │  App Runner: pmguru-web  │   (Next.js 14 standalone, :3000)
                         │  env: BRAIN_URL          │
                         └───────────┬──────────────┘
                                     │  server-side /api/* proxy
                                     ▼
                         ┌─────────────────────────┐        ┌────────────────────────┐
                         │ App Runner: pmguru-brain │ ─────▶ │  RDS / Aurora Postgres  │
                         │ Python http.server :8000 │        │  (DATABASE_URL)         │
                         │ env: GROQ_API_KEY,       │        └────────────────────────┘
                         │      DATABASE_URL        │
                         └─────────────────────────┘
```

- **Brain (backend)** — `backend/`, a deterministic consulting engine (`ThreadingHTTPServer`,
  binds `0.0.0.0:$PORT`). Pure-Python; needs **no** LLM key to work (Groq only polishes).
- **Web (frontend)** — `frontend/`, Next.js 14 standalone. Talks to the brain via `BRAIN_URL`
  (server-side `/api/*` proxies — the browser never calls the brain directly).
- **Database** — RDS/Aurora PostgreSQL. Set `DATABASE_URL` on the brain and the Engagement
  Digital Twin persists in Postgres automatically; unset and it falls back to a JSONL file.

## Environment contract

| Service | Var | Value | Notes |
|---|---|---|---|
| brain | `PORT` | `8000` | App Runner forwards this |
| brain | `GROQ_API_KEY` | `<key>` | optional — deterministic core works without it |
| brain | `DATABASE_URL` | `postgresql://user:pass@host:5432/pmguru` | enables Postgres twin store |
| brain | `BRAIN_DATA_DIR` | `/data` | JSONL fallback (docs/learning); ephemeral unless EFS-mounted |
| web | `BRAIN_URL` | `https://<brain-apprunner-url>` | **https, no trailing slash** |
| web | `PORT` | `3000` | App Runner forwards this |

---

## Path A — containers via ECR + App Runner (recommended, reproducible)

Both services have production `Dockerfile`s (`backend/Dockerfile`, `frontend/Dockerfile`).

```bash
export AWS_REGION=ap-south-1
export ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export ECR=$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# 1. ECR repos
aws ecr create-repository --repository-name pmguru-backend  --region $AWS_REGION || true
aws ecr create-repository --repository-name pmguru-frontend --region $AWS_REGION || true
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR

# 2. Build + push (run where Docker is available — local, EC2, or CodeBuild)
docker build -t $ECR/pmguru-backend:latest  ./backend
docker build -t $ECR/pmguru-frontend:latest ./frontend
docker push $ECR/pmguru-backend:latest
docker push $ECR/pmguru-frontend:latest
```

Then create the two App Runner services from the images (console or `aws apprunner
create-service`), wiring the env vars above. The brain's health-check path is **`/health`**;
the web's is **`/`**. Deploy the **brain first**, copy its URL into the web's `BRAIN_URL`.
`deploy/aws-deploy.sh` automates the build/push (and prints next steps).

> No Docker on the build host? Use **AWS CodeBuild** (a buildspec that runs the same
> `docker build/push`), or use **Path B** below (App Runner builds from source, no Docker).

## Path B — App Runner from source (no Docker)

Each service ships an `apprunner.yaml` (managed runtime). In App Runner: *Create service →
Source: this GitHub repo →* set **Source directory** to `backend` (brain) or `frontend` (web),
keep "Use a configuration file", add the env vars, deploy. Brain first, then web with `BRAIN_URL`.

## Database (RDS / Aurora Postgres)

```bash
aws rds create-db-instance \
  --db-instance-identifier pmguru-pg --engine postgres --engine-version 15 \
  --db-instance-class db.t3.micro --allocated-storage 20 \
  --master-username pmguru --master-user-password '<STRONG_PW>' \
  --db-name pmguru --region $AWS_REGION
```

Put the brain and RDS in the same VPC (App Runner VPC connector), then set
`DATABASE_URL=postgresql://pmguru:<pw>@<rds-endpoint>:5432/pmguru` on the brain. The twin table
is auto-created on first write. **Verify:** `GET /engagements/tests` reports `"backend": "postgres"`.

## Verify the chain

```bash
curl https://<brain-url>/health     # → {"status":"ok", ... advertises all layers}
# open https://<web-url>/engage  → run an engagement → it persists (twin_id) in Postgres
```

## Known production notes
- The brain is `ThreadingHTTPServer` (handles concurrency). Fine for App Runner autoscaling;
  revisit a WSGI/ASGI server only at high sustained load.
- With `DATABASE_URL` set, the **twin** persists in Postgres. `doc_store` (RAG corpus) and the
  `live_brain` learning log are still JSONL under `BRAIN_DATA_DIR` — mount **EFS** at `/data` to
  persist them, or migrate them to Postgres/S3 next (see `docs/CONSULTING-OS.md`).
- Secrets (`GROQ_API_KEY`, `DATABASE_URL`) → App Runner env or **AWS Secrets Manager**.
- HTTPS/custom domain → App Runner custom domains; WAF/Cognito are the next hardening step.
