# Start MotionGuard AI Enterprise

## Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_backend.py
```

Backend runs at `http://127.0.0.1:8000`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173`.

## First Test

1. Create User A on `/signup`.
2. Create a zone on `/zones`.
3. Verify the account using the Firebase verification email.
4. Upload a video on `/live-monitoring`.
5. Review incidents, evidence, analytics, assistant answers, and reports.
6. Log out from `/settings`.
7. Create User B and confirm data starts empty.
