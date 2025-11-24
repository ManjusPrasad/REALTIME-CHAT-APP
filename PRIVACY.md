# Privacy Notice — Real-time Chat Application

Last updated: November 24, 2025

This document explains how this demo real-time chat application handles data, privacy expectations, and recommendations if you deploy it to production.

## Summary (short)
- Messages are ephemeral by design and not persisted unless explicitly implemented.
- The application does not capture or store screenshots. However, it cannot prevent users from using their device or OS to take screenshots.
- Media (images/videos) uploaded through the app are stored in the `uploads/` folder by the server. On most hosting platforms (including Railway), this storage is ephemeral: files may be lost on restart or redeploy.
- No personal data is collected by default beyond the username and lightweight metadata required for chat operation (timestamp for ordering, message id for reactions).

## What we store (current behavior)
- Username (provided by the web client) — used to identify messages in the room.
- Message content (in-memory or short-lived storage) for broadcast and reaction handling.
- Reactions and small metadata required to keep clients in sync.
- Uploaded media files saved under `uploads/` directory (ephemeral).

## What we do NOT do
- We do not capture or record screenshots of user screens.
- We do not record audio, access camera, or scan local files without explicit user interaction.
- We do not sell or share personal data with third parties.

## Privacy limitations and important notes
- Client-side screenshots: Browsers cannot prevent OS-level screenshots. The policy clarifies the app's behavior (it does not capture nor store screenshots) but cannot technically block users from taking screenshots on their device.
- Upload persistence: On ephemeral hosting (Railway, Heroku, etc.), uploaded files are not persistent across restarts. For production, we recommend using S3 or other object storage.
- Authentication: This demo does not include authentication. Adding authentication is strongly recommended for production to control access to private rooms and media.

## Recommendations for production
1. Move media storage to a persistent object store (Amazon S3, Google Cloud Storage, or equivalent). Use presigned URLs for secure uploads.
2. Add authentication (OAuth, JWT) and access control (room membership checks on the server-side).
3. Consider end-to-end encryption (E2EE) for highly sensitive conversations.
4. Add retention policies: allow users to opt-in to store history, or enforce automatic deletion after a TTL.
5. Add monitoring and logging (only metadata, not message content unless required and consented).

## Contact
If you have questions about privacy or need changes to the policy, contact the project owner (ManjusPrasad) via the repository contact details.

---
This is a simple privacy notice intended for demo projects. For legal compliance (GDPR, CCPA), consult a privacy professional and adapt the policy to your jurisdiction and use case.
