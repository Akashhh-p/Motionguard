# MotionGuard AI Enterprise

MotionGuard AI Enterprise is a production-style AI video intelligence platform built from the original MotionGuard OpenCV/YOLOv8 project. It supports authenticated multi-user surveillance workflows: video uploads, webcam monitoring, virtual restricted zones, intrusion incidents, evidence screenshots, analytics, and daily PDF/CSV reports.

## Why It Is Different

The original project was a script-based computer vision demo. This version is a full-stack SaaS-style application with real Firebase Authentication, backend Firebase ID token verification, user-scoped database records, user-scoped file storage, FastAPI services, SQLAlchemy models, and a responsive TypeScript dashboard.

## Features

- Email/password signup and login through Firebase Authentication
- Google login through Firebase Authentication
- FastAPI verification of Firebase ID tokens with Firebase Admin SDK
- Protected APIs and protected frontend routes
- Per-user incidents, detections, zones, videos, settings, screenshots, and reports
- YOLOv8 object detection for uploaded videos and webcam streams
- Virtual polygon zones with intrusion detection for people
- Evidence screenshot capture with incident cooldown
- Incident filters, CSV export, evidence viewing, and resolution
- Analytics summary and charts
- Professional daily PDF and CSV report generation
- Premium responsive dashboard for desktop, tablet, and mobile

## Tech Stack

Backend: FastAPI, Python, OpenCV, Ultralytics YOLOv8, SQLAlchemy, SQLite, Firebase Admin SDK, ReportLab.

Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts, Axios, React Router, lucide-react.

Database: SQLite by default, with SQLAlchemy models designed to be PostgreSQL migration-ready.

## Folder Structure

```text
backend/app
  routes/       API route modules
  services/     YOLO, video, incident, analytics, reports, settings
  utils/        file, geometry, time helpers
frontend/src
  components/   shared UI
  context/      auth state
  layouts/      SaaS dashboard shell
  pages/        landing, auth, dashboard, monitoring, zones, incidents, reports, settings
backend/storage
  uploads/      uploaded videos
  evidence/     incident screenshots
  reports/      generated PDF/CSV reports
  outbox/       development verification/reset email log
```

## Installation

Copy environment defaults:

```bash
copy .env.example .env
```

Firebase setup:

1. Create a Firebase project.
2. Enable **Authentication** -> **Sign-in method** -> **Email/Password**.
3. Enable **Google** sign-in.
4. Add `localhost` and `127.0.0.1` as authorized domains.
5. Copy the Firebase web app config into the `VITE_FIREBASE_*` values.
6. Create a Firebase service account JSON from **Project settings** -> **Service accounts**.
7. Save that JSON outside Git and set `FIREBASE_SERVICE_ACCOUNT_PATH` to its absolute path.
8. Set `FIREBASE_PROJECT_ID`.

## Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_backend.py
```

Backend: `http://127.0.0.1:8000`

Health check: `http://127.0.0.1:8000/health`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://127.0.0.1:5173`

## How To Use

1. Open `/signup` and create an account.
2. Open `backend/storage/outbox/email_outbox.log` and use the verification link.
3. Create a virtual zone on `/zones`.
4. Upload a video on `/live-monitoring`.
5. Review incidents on `/incidents` and evidence on `/evidence`.
6. Ask analytics questions on `/assistant`.
7. Generate a daily report on `/reports`.
8. Configure thresholds, dashboard preferences, classes, alerts, and logout on `/settings`.

## Webcam

Open `/live-monitoring` and select Start webcam. The backend opens the local camera, runs YOLOv8, stores detections for the logged-in user, and streams annotated MJPEG frames to the UI. If the camera is missing or busy, the status panel shows an error instead of crashing.

## Restricted Zones

Zones are stored as user-scoped polygons. During video analysis, MotionGuard calculates each detected person's bounding-box center. If that point falls inside a saved zone, the incident engine creates an `Unauthorized Intrusion` incident and saves a screenshot in shared managed storage. Evidence access is controlled by the database: the `evidence.user_id` and linked incident ownership must match the authenticated user.

## API Overview

Auth:

- `POST /api/auth/session`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Firebase handles email/password signup, email/password login, Google login, forgot password, password reset emails, and secure browser session state. The frontend sends Firebase ID tokens to FastAPI. FastAPI verifies those tokens before returning user-scoped application data.

Detection:

- `POST /api/detection/upload-video`
- `POST /api/detection/start-webcam`
- `POST /api/detection/stop-webcam`
- `GET /api/detection/status`
- `GET /api/detection/webcam-stream`

Zones, incidents, analytics, reports, and settings:

- `POST /api/zones`, `GET /api/zones`, `PUT /api/zones/{id}`, `DELETE /api/zones/{id}`
- `GET /api/incidents`, `GET /api/incidents/{id}`, `PUT /api/incidents/{id}/resolve`, `DELETE /api/incidents/{id}`
- `GET /api/analytics/summary`, `GET /api/analytics/charts`
- `GET /api/analytics/daily-summary`
- `GET /api/evidence`, `DELETE /api/evidence/{id}`
- `POST /api/assistant/ask`
- `POST /api/reports/generate`, `GET /api/reports`, `GET /api/reports/{id}/download`
- `GET /api/settings`, `PUT /api/settings`

## Sample Video Testing

Place test videos in `sample_videos/`, then upload them from `/live-monitoring`. Supported formats are `.mp4`, `.avi`, `.mov`, `.mkv`, and `.webm`.

## Docker

```bash
docker compose up --build
```

## Screenshots

Add project screenshots here after running the app locally:

- Landing page
- Dashboard
- Live monitoring
- Zone editor
- Incidents
- Reports

## Troubleshooting

- Webcam not found: confirm the camera index and close other apps using the camera.
- YOLO model missing: ensure `yolov8n.pt` exists at the project root or set `YOLO_MODEL_PATH`.
- Upload rejected: check the file extension and size.
- Firebase auth unavailable: set `FIREBASE_SERVICE_ACCOUNT_PATH`, `FIREBASE_PROJECT_ID`, and all `VITE_FIREBASE_*` values.
- Empty dashboard: each new user starts with isolated data.
- Database issues: delete `backend/motionguard.db` only if you intentionally want a clean local database.

## Future Improvements

- PostgreSQL migration with Alembic
- Role-based organization teams
- Telegram alerts
- Background queue for long video processing
- Camera RTSP sources
- Rich report templates with embedded evidence thumbnails
