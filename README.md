# Real-time Chat Application

A real-time chat application with reaction support built using FastAPI and WebSockets.

## Features

- Real-time messaging
- Multiple chat rooms
- User presence (join/leave notifications)
- Message reactions with emojis
- Modern, responsive UI

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

## Testing

Run the test suite:
```bash
python test_reactions.py
```

Run the demo script:
```bash
python demo_reaction_updates.py
```