# Privacy Notice — Real-time Chat Application

Last updated: November 25, 2025

This is a concise, app-focused privacy statement for this demo chat application. It describes only the app's behavior and what data the app stores or transmits.

## Key points
- The app requires a username to join a room and uses it to label messages.
- Messages are transient by default: message content is kept in memory for broadcasting and is not stored as a durable chat history by this demo.
- Uploaded media (images/videos) are saved to the server `uploads/` directory. On many hosting platforms (including Railway) this storage is ephemeral and may be lost on restart or redeploy.
- The app does not collect additional personal data beyond the username and lightweight metadata (timestamps, message ids) needed for chat functionality.

## What the app does not do
- This demo does not sell or share user data with third parties.
- The app does not record audio or access the camera unless a user explicitly uploads media.

## Production considerations
- For persistent media storage in production, use object storage (e.g., Amazon S3) and presigned upload URLs.
- Add authentication (JWT/OAuth) and server-side access control to protect private rooms and media in production.

If you need a more detailed legal privacy policy for production use (GDPR/CCPA), consult legal counsel. This document is intentionally short and focused on the app's observable behavior.
