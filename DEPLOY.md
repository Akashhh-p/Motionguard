# MotionGuard Deployment

This production setup runs the FastAPI backend and React frontend with Docker Compose. Nginx serves the frontend and proxies `/api` plus `/health` to the backend container.

## 1. Server Prerequisites

Install Docker and the Docker Compose plugin on your VPS. Open inbound ports `80` and, if you add TLS later, `443`.

## 2. Prepare Environment

Create the production environment file:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` with your real domain and Firebase web app values. Use a strong random value for `JWT_SECRET_KEY`.

Create the Firebase Admin secret file:

```bash
mkdir -p secrets
```

Save your Firebase service account JSON as:

```text
secrets/firebase-service-account.json
```

Do not commit `.env.production` or anything in `secrets/`.

## 3. Firebase Console

In Firebase Authentication, add your production domain to **Authorized domains**. If you test by IP address first, add that host too.

## 4. Build And Run

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

Check the app:

```bash
docker compose -f docker-compose.prod.yml ps
curl http://your-domain.com/health
```

Open:

```text
http://your-domain.com
```

## 5. Logs And Updates

View logs:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

Deploy a new version:

```bash
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

## 6. HTTPS

For production, put Cloudflare, Caddy, Traefik, or an Nginx reverse proxy with Let's Encrypt in front of this compose stack. After HTTPS is active, update:

```text
FRONTEND_URL=https://your-domain.com
CORS_ORIGINS=https://your-domain.com
```
