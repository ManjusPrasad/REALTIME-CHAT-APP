# Architecture — Real-time Chat Application

## Overview
This is a lightweight real-time chat application using FastAPI (backend) and vanilla JavaScript (frontend). The app focuses on WebSocket-based messaging with reaction support and simple media uploads.

## Components
- Backend (FastAPI)
  - WebSocket endpoint: `/ws/{room}/{username}` — real-time messaging and reaction events.
  - Upload endpoint: `POST /upload` — receives multipart file upload and saves to `uploads/`.
  - Health endpoint: `GET /health` — returns `{ "status": "ok" }` (used by Railway healthchecks).
  - Static and uploads serving: `/static/*` and `/uploads/*` (served by Starlette's StaticFiles).
- Frontend
  - `templates/index.html` — single page UI.
  - `static/app.js` — client logic for connecting WebSocket, rendering messages, reactions, and handling uploads.
- Models
  - `app/schemas.py` — Pydantic models for Message, MessageBroadcast, ReactionRequest, etc.

## Data flow
1. Client opens WebSocket to `/ws/{room}/{username}`.
2. Client sends `{ type: 'message', content }` via WebSocket to create a message.
3. Server assigns message id, stores in short-lived in-memory structure for reaction handling, then broadcasts to other clients in the same room.
4. For media: client uploads file to `/upload` via HTTP POST; server returns `url`; client sends a WebSocket message with `content` set to an `<img>` or `<video>` tag pointing to that URL; server broadcasts like a normal message.

## Deployment
- `railway.json` contains `startCommand: uvicorn app.main:app --host 0.0.0.0 --port ${PORT}` and `healthcheckPath: /health` (recommended).
- `requirements.txt` includes `aiofiles` which is required by Starlette's StaticFiles in production.
- For production readiness:
  - Replace local `uploads/` with S3 or equivalent. Use presigned upload URLs from the server to the client.
  - Add authentication (JWT/OAuth) for private rooms.
  - Use Redis or other Pub/Sub to scale WebSocket broadcast across multiple app instances.

## Security recommendations
- Validate and sanitize all incoming messages and uploaded file names.
- Limit allowed MIME types and file sizes for uploads (e.g., 10–20 MB max) and scan files if possible.
- Use HTTPS in production (Railway provides TLS). WebSocket should use `wss://` behind TLS.
- Rate-limit WebSocket actions to prevent abuse.
- Add server-side checks to ensure a user only performs actions they are authorized for.

## Scaling
- Single-instance works for small usage. To scale:
  - Use Redis (PUB/SUB) for broadcasting messages between processes.
  - Move persistent data to a database (Postgres) and media to object storage (S3).
  - Add a lightweight job queue (RQ/Celery) for background tasks like thumbnail generation.

## Local development
1. Create a virtual environment and install dependencies from `requirements.txt`.
2. Start the app locally:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
3. Open `http://127.0.0.1:8000` in your browser.

## Tests
- `test_reactions.py` and `demo_reaction_updates.py` provide simple test/demos for reaction handling — run them locally when server is running.

## Next steps
- Add authentication and authorization.
- Switch uploads to S3 with presigned URLs.
- Add a Redis-backed broadcast layer for multi-instance deployment.
- Implement end-to-end encryption for private rooms if required.

