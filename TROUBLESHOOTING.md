# Troubleshooting Guide

## ERR_BLOCKED_BY_CLIENT Error

If you see `net::ERR_BLOCKED_BY_CLIENT` errors in the browser console:

### Cause
Browser extensions (ad blockers, privacy tools) are blocking Firebase requests.

### Solutions

**Option 1: Disable Ad Blocker for localhost**
1. Click your ad blocker extension icon (e.g., uBlock Origin, AdBlock Plus)
2. Disable it for `localhost` or `127.0.0.1`
3. Refresh the page

**Option 2: Whitelist Firebase Domains**
Add these domains to your ad blocker whitelist:
- `firestore.googleapis.com`
- `firebase.googleapis.com`
- `firebasestorage.googleapis.com`

**Option 3: Use Incognito/Private Mode**
Open the app in incognito mode with extensions disabled:
- Chrome: Ctrl+Shift+N
- Firefox: Ctrl+Shift+P
- Edge: Ctrl+Shift+N

## Cross-Origin-Opener-Policy Warning

The "Cross-Origin-Opener-Policy policy would block the window.closed call" warning is harmless and doesn't affect functionality. It's related to Firebase Auth popup detection.

## Missing or Insufficient Permissions

If you get Firestore permission errors:
1. Make sure you've deployed the latest rules: `firebase deploy --only firestore:rules`
2. Ensure you're logged in as a doctor when uploading records
3. Check that the patient email exists in the system

## Backend Not Starting

If backend fails to start:
1. Create `backend/.env` file (copy from `.env.example`)
2. Install dependencies: `pip install -r requirements.txt`
3. Start with: `python -m uvicorn app.main:app --reload --port 8000`

## Frontend Not Starting

If frontend fails to start:
1. Install dependencies: `npm install`
2. Create `frontend/.env` file (copy from `.env.example`)
3. Start with: `npm run dev`
