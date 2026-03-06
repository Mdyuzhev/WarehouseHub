# TASK: Add Homelab Docker Compose Deploy — Remove GitLab/K3s

## Context

The project has two deploy targets:
- **Homelab** (192.168.1.74) — local server, Docker installed, no K3s
- **Yandex Cloud** (wh-lab.ru) — already works via `production/docker-compose.yml` + GitHub Actions

**What changes:** Remove GitLab CI and K3s entirely. Add homelab as a deploy target.
**What stays:** `production/` directory and Yandex Cloud workflow stay untouched.

## Goal

- `docker compose up --build` starts the full stack on homelab
- Push to `main` on GitHub → GitHub Actions → SSH to homelab → `git pull && docker compose up --build`
- Yandex Cloud deploy continues to work as before (do not touch)

## Done When

- `curl http://192.168.1.74:8080/actuator/health` returns 200
- `curl http://192.168.1.74` returns frontend
- No `kubectl`, `k3s`, `cr.yandex` references remain in active files
- GitHub Actions has a working homelab deploy job

---

## Step 1 — Delete (no backup needed)

```
.gitlab-ci.yml                        ← root GitLab orchestrator
api/.gitlab-ci.yml                    ← api pipeline
api/.gitlab/                          ← GitLab MR templates
frontend/.gitlab-ci.yml               ← frontend pipeline
testing/.gitlab-ci.yml                ← testing pipeline
k8s/                                  ← all Kubernetes manifests
.github/workflows/manual-deploy.yml  ← staging deploy references K3s
```

Do not touch:
- `production/` — Yandex Cloud config, keep as is
- `.github/workflows/deploy-prod.yml` — Yandex Cloud deploy, will be extended in Step 4

---

## Step 2 — Create root docker-compose.yml

Create `docker-compose.yml` at repo root.
This is for homelab only. Builds from local Dockerfiles (no registry pull).

```yaml
services:
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: warehouse-api
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/warehouse
      - SPRING_DATASOURCE_USERNAME=warehouse
      - SPRING_DATASOURCE_PASSWORD=${DB_PASSWORD}
      - SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE=15
      - SPRING_DATASOURCE_HIKARI_MINIMUM_IDLE=5
      - SPRING_DATASOURCE_HIKARI_CONNECTION_TIMEOUT=30000
      - SPRING_DATA_REDIS_HOST=redis
      - SPRING_DATA_REDIS_PORT=6379
      - SPRING_CACHE_TYPE=redis
      - SPRING_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - JWT_SECRET=${JWT_SECRET}
    ports:
      - "8080:8080"
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: warehouse-frontend
    ports:
      - "80:80"
    restart: unless-stopped
    depends_on:
      - api

  analytics:
    build:
      context: ./analytics-service
      dockerfile: Dockerfile
    container_name: warehouse-analytics
    environment:
      - ANALYTICS_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - ANALYTICS_REDIS_HOST=redis
      - ANALYTICS_REDIS_PORT=6379
    ports:
      - "8090:8090"
    restart: unless-stopped
    depends_on:
      kafka:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8090/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  db:
    image: postgres:15-alpine
    container_name: warehouse-db
    environment:
      - POSTGRES_DB=warehouse
      - POSTGRES_USER=warehouse
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U warehouse -d warehouse"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: warehouse-redis
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  kafka:
    image: apache/kafka:3.7.0
    container_name: warehouse-kafka
    environment:
      - KAFKA_NODE_ID=1
      - KAFKA_PROCESS_ROLES=broker,controller
      - KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
      - KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
      - KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT
      - KAFKA_AUTO_CREATE_TOPICS_ENABLE=true
      - KAFKA_NUM_PARTITIONS=3
      - KAFKA_DEFAULT_REPLICATION_FACTOR=1
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
      - CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk
    volumes:
      - kafka_data:/var/lib/kafka/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

volumes:
  postgres_data:
  redis_data:
  kafka_data:
```

---

## Step 3 — Create .env.example at repo root

```
# Copy to .env — never commit .env to git

# Database password
DB_PASSWORD=change_me_strong_password

# JWT secret (generate: openssl rand -base64 64)
JWT_SECRET=change_me_generate_new_secret
```

Verify `.env` is in root `.gitignore` (it should already be there).

---

## Step 4 — Add homelab job to existing GitHub Actions workflow

Open `.github/workflows/deploy-prod.yml`.
Do NOT rewrite it — just add a new job `deploy-homelab` alongside the existing `deploy` job.

```yaml
  deploy-homelab:
    name: Deploy to Homelab
    runs-on: ubuntu-latest
    environment: homelab

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.HOMELAB_HOST }}
          username: ${{ secrets.HOMELAB_USER }}
          key: ${{ secrets.HOMELAB_SSH_KEY }}
          script: |
            cd /opt/warehouse
            git pull origin main
            docker compose up --build -d
            docker image prune -f
            echo "Deployed at $(date)"

      - name: Health check
        run: |
          sleep 30
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            http://${{ secrets.HOMELAB_HOST }}:8080/actuator/health || echo "000")
          if [ "$STATUS" = "200" ]; then
            echo "API healthy"
          else
            echo "API returned $STATUS"
            exit 1
          fi
```

The existing `deploy` job (Yandex Cloud) must remain exactly as is.

---

## Step 5 — Fix telegram-bot/Dockerfile

Current Dockerfile installs `kubectl` — not needed without K3s.
Replace with clean version:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py .
COPY app.py .
COPY bot/ ./bot/
COPY services/ ./services/

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Step 6 — Fix orchestrator-ui/Dockerfile

Also installs `kubectl` — remove it:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Constraints

- Do NOT touch `production/` directory — it's for Yandex Cloud
- Do NOT touch the existing `deploy` job in `deploy-prod.yml`
- Do NOT add `telegram-bot`, `warehouse-robot`, `orchestrator-ui` to root `docker-compose.yml` — optional services, not core stack
- Do NOT add nginx to root `docker-compose.yml` — homelab uses direct ports, no SSL

---

## After the task — user must do manually

**GitHub Secrets** (Settings → Secrets → Actions → New repository secret):

| Secret | Value |
|--------|-------|
| `HOMELAB_HOST` | `192.168.1.74` |
| `HOMELAB_USER` | SSH username on the server |
| `HOMELAB_SSH_KEY` | Private SSH key (the key whose public part is in server's authorized_keys) |

**On the server (192.168.1.74):**
```bash
git clone https://github.com/Mdyuzhev/WarehouseHub.git /opt/warehouse
cd /opt/warehouse
cp .env.example .env
# Edit .env — set real DB_PASSWORD and JWT_SECRET
```
