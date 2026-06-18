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
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

If you do not use `Root Directory: backend`, use these commands instead:

```text
Build Command: pip install -r backend/requirements.txt
Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
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

Your deploy log shows Render is using a Python version where `torch==2.1.1` is unavailable. Fix it by setting this backend environment variable and redeploying:

```text
PYTHON_VERSION=3.11.11
```

The `.python-version` files in this repo also pin the version for future deploys.
