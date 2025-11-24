# Real-time Chat Application

A real-time chat application with reaction support built using FastAPI and WebSockets.

## Features

- Real-time messaging
- Multiple chat rooms
- User presence (join/leave notifications)
- Message reactions with emojis
- Modern, responsive UI
 - No chat history is stored (ephemeral messaging)
 - Does not capture or store screenshots; cannot prevent device screenshots
 - Private chat rooms
 - Share images and videos
 - Copyright © 2025 ManjusPrasad. All rights reserved.

## Tech Stack

- Backend: FastAPI
- Frontend: HTML, CSS, JavaScript
- WebSockets for real-time communication
- Pydantic for data validation

## Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd realtime-chat-app
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn app.main:app --reload
```

4. Visit http://localhost:8000 in your browser

## Deployment

### Railway Deployment

Live app: https://web-production-aa93.up.railway.app/

1. Install Railway CLI:
```bash
# On Windows
winget install Railway.CLI

# On macOS
brew install railway
```

2. Login to Railway:
```bash
railway login
```

3. Initialize project:
```bash
railway init
```

4. Deploy the application:
```bash
railway up
```

### Environment Variables

- `PORT` - Port number (set automatically by Railway)

## Download APK

If you want to install the Android app directly, download the APK here:

- Official APK: https://warehouse.appilix.com/uploads/app-apk-692332f389054-1763914483.apk

Note: Only install APKs from trusted sources. Installing APKs from unknown sources may pose security risks.

## Testing

Run the test suite:
```bash
python test_reactions.py
```

Run the demo script:
```bash
python demo_reaction_updates.py
```

## Project Analysis

Overview:
- This project is a lightweight real-time chat application built with FastAPI (backend) and plain HTML/CSS/JavaScript (frontend). It uses WebSockets for low-latency message delivery.

Architecture & components:
- Backend: `app/main.py` (FastAPI) — provides WebSocket endpoints, an upload HTTP endpoint (`/upload`), and a lightweight `/health` endpoint used for platform healthchecks.
- Frontend: `templates/index.html` + `static/app.js` — a single-page UI that connects via WebSocket and supports message reactions, image/video uploads, and ephemeral chat UI.
- Models: `app/schemas.py` — Pydantic models for message, reactions and broadcast payloads.

Privacy & Security (valid points):
- Ephemeral messaging by default — messages are intended to be transient; server-side storage is minimal and used for reaction updates and short-term functionality.
- The app does not capture or store screenshots; however, it cannot technically prevent users from taking screenshots with their device/OS.
- Media uploads are served from the `uploads/` directory; this storage is ephemeral on Railway. For production use, migrate media to a persistent store (S3) and use signed URLs.
- No authentication is present; consider adding user authentication (OAuth/JWT) and access control for private rooms.

Scalability & reliability suggestions:
- Use Redis (PUB/SUB) or a message broker for scaling WebSocket broadcasts across multiple instances.
- Add persistent storage for messages and media if you need durable history (e.g., PostgreSQL + S3).
- Add rate-limiting and input validation to avoid abuse.

Deployment notes:
- `railway.json` contains a `startCommand` for `uvicorn` and a `healthcheckPath` set to `/health`.
- `requirements.txt` includes `aiofiles` for static file support.

Next steps / roadmap:
- Add authentication and user profiles.
- Add optional message persistence with user consent (toggle to save chat history).
- Implement E2E encryption for private rooms if high confidentiality is required.
- Move file uploads to persistent object storage with signed URLs.
- Add unit/integration tests for WebSocket handlers and reaction logic.

If you want, I can open a new `DOCS.md` or `ARCHITECTURE.md` file with diagrams and explicit instructions for production hardening.