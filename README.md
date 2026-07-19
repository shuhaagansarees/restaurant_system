# Restaurant Operating System

A fully-featured Restaurant OS built with Flask, SQLAlchemy, SQLite, and WebSockets.
Features include a customer ordering PWA, admin real-time Live Orders Kanban, KDS, Billing, and Analytics.

## Deployment on Render.com (Free Tier)

This application is configured to run smoothly on Render's Web Service free tier.

**Start Command:**
Configure the web service on Render to use this exact start command:
```bash
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 app:app
```
*(This ensures `flask-socketio` works properly with WebSockets enabled rather than polling.)*

**Known Limitations on Free Tier (IMPORTANT):**
Render's free tier uses an **ephemeral disk**. This means every time the server spins down or restarts, any local file changes made during runtime (like `restaurant.db` updates or activity logs) will be reset.
* For a true production deployment, you MUST either upgrade to a paid persistent disk on Render or migrate the SQLite database to a managed PostgreSQL instance (e.g. Supabase, Render PostgreSQL). SQLAlchemy supports this seamlessly.

## Environment Variables
Create a `.env` file or provide these in the Render dashboard:
* `SECRET_KEY`: A strong random string for Flask sessions.
* `UPI_ID`: Your merchant UPI ID for dynamic QR generation.
* `RESTAURANT_NAME`: Name displayed on the UI and QR code.
* `WHATSAPP_TOKEN` / `WHATSAPP_PHONE_ID`: For Facebook Graph API notifications.

## Pushing to GitHub

To push this codebase to your own GitHub repository, run the following commands in your terminal:

```bash
git init
git add .
git commit -m "Initial commit of Restaurant OS"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```
