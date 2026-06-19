# MotionGuard Render Deployment

Render currently defaults new Python services to a newer Python version than this app's pinned Torch/Ultralytics dependencies support. This repo pins Python to `3.11.11` with `.python-version` files.

## Backend Web Service

Create a new **Web Service** on Render from:

```text
https://github.com/Akashhh-p/Motionguard
```

Recommended backend settings:

```text
Name: motionguard-backend
Runtime: Python 3
Root Directory: leave blank
Build Command: pip install -r backend/requirements.txt
Start Command: python render_start.py
Health Check Path: /health
```

Alternative settings if you set `Root Directory` to `backend`:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Backend Environment

Add these environment variables to the backend service:

```text
PYTHON_VERSION=3.11.11
JWT_SECRET_KEY=replace-with-a-long-random-secret
FRONTEND_URL=https://your-frontend-service.onrender.com
CORS_ORIGINS=https://your-frontend-service.onrender.com
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=/etc/secrets/firebase-service-account.json
```

In the backend service **Environment** tab, add a Render **Secret File**:

```text
Filename: firebase-service-account.json
Contents: your Firebase Admin SDK service account JSON
```

Render exposes secret files at `/etc/secrets/<filename>`.

Alternatively, if secret files are awkward, add one environment variable instead:

```text
FIREBASE_SERVICE_ACCOUNT_JSON=<paste the full Firebase Admin SDK JSON on one line>
```

Use either `FIREBASE_SERVICE_ACCOUNT_PATH` with a Render secret file or `FIREBASE_SERVICE_ACCOUNT_JSON`. The JSON env var takes precedence when both are set.

## Frontend Static Site

Create a new **Static Site** on Render from the same repo.

Recommended frontend settings:

```text
Name: motionguard-frontend
Root Directory: frontend
Build Command: npm install && npm run build
Publish Directory: dist
```

Add these frontend environment variables before building:

```text
VITE_API_URL=https://your-backend-service.onrender.com/api
VITE_FIREBASE_API_KEY=your-firebase-web-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-firebase-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-firebase-app-id
```

## Firebase Console

In Firebase Authentication, add your Render frontend domain:

```text
your-frontend-service.onrender.com
```

Also add your custom domain later if you connect one.

## Fix For Your Current Error

If Render logs show `Timed Out` after `No open ports detected`, redeploy the latest commit. The backend no longer loads YOLO during FastAPI startup, so Render can detect the web port quickly. YOLO loads lazily when you use detection features.

If Render logs show `ModuleNotFoundError: No module named 'app'`, your backend service is starting from the repo root with `uvicorn app.main:app`. Use:

```text
Build Command: pip install -r backend/requirements.txt
Start Command: python render_start.py
```

The repo also includes a root-level compatibility module, so `uvicorn app.main:app --host 0.0.0.0 --port $PORT` works from the repo root after this commit. `python render_start.py` is still the preferred Render start command because it is explicit.

If Render logs show `POST /auth/session HTTP/1.1" 404 Not Found`, the frontend was built with an API URL that missed the `/api` prefix. Set `VITE_API_URL=https://your-backend-service.onrender.com/api` and redeploy the frontend. The frontend also normalizes a backend root URL to `/api` as a guardrail.

If Render logs show `torch==2.1.1` is unavailable, set this backend environment variable and redeploy:

```text
PYTHON_VERSION=3.11.11
```

The `.python-version` files in this repo also pin the version for future deploys.
