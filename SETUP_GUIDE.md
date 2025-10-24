# Quick Setup Guide

## Step-by-Step Setup (15 minutes)

### 1. Firebase Project Setup (5 min)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or select existing
3. Enable services:
   - **Authentication**: 
     - Click "Get started"
     - Enable "Google" sign-in method
   - **Firestore Database**:
     - Create database in production mode
     - Choose region (e.g., us-central1)
   - **Storage**:
     - Get started with default settings

4. Get Firebase config:
   - Project Settings → General → Your apps
   - Click "Web" icon (</>) to add web app
   - Copy the config object

5. Generate service account (for backend):
   - Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file securely

### 2. Frontend Setup (5 min)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
copy .env.example .env.local

# Edit .env.local with your Firebase config
# (Use notepad, VS Code, or any text editor)
notepad .env.local
```

Paste your Firebase config:
```env
VITE_FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abcdef123456
VITE_BACKEND_URL=http://localhost:8000
```

```bash
# Start development server
npm run dev
```

Frontend is now running at http://localhost:5173

### 3. Deploy Firebase Rules (2 min)

```bash
# Install Firebase CLI (if not installed)
npm install -g firebase-tools

# Login
firebase login

# Initialize (from project root: ebooklet/)
cd ..
firebase init

# Select:
# - Firestore
# - Storage
# Choose existing project
# Use existing firestore.rules and storage.rules

# Deploy rules
firebase deploy --only firestore:rules,storage:rules
```

### 4. Backend Setup (Optional - 3 min)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env

# Edit .env
notepad .env
```

Paste your config:
```env
ALLOWED_ORIGINS=http://localhost:5173
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id",...}
FIREBASE_PROJECT_ID=your-project-id
BASE_APP_URL=http://localhost:5173
NOTIFY_CHANNELS=email
SENDGRID_API_KEY=SG.your_key_here
SENDGRID_FROM_EMAIL=notifications@yourdomain.com
```

```bash
# Start backend
uvicorn app.main:app --reload --port 8000
```

Backend is now running at http://localhost:8000

### 5. Test the Application

1. Open http://localhost:5173
2. Click "Sign in with Google"
3. Select role: Doctor or Patient
4. **As Doctor**:
   - Upload a test file
   - Enter patient email (must be a registered patient)
5. **As Patient**:
   - View uploaded records
   - Download files

## Quick Commands Reference

### Frontend
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
```

### Backend
```bash
cd backend
pip install -r requirements.txt    # Install dependencies
uvicorn app.main:app --reload      # Start dev server
uvicorn app.main:app --host 0.0.0.0 --port 8000  # Production
```

### Firebase
```bash
firebase login                                    # Login
firebase init                                     # Initialize project
firebase deploy --only firestore:rules           # Deploy Firestore rules
firebase deploy --only storage:rules             # Deploy Storage rules
firebase deploy --only hosting                   # Deploy frontend
firebase emulators:start                         # Start local emulators
```

## Testing Checklist

- [ ] Can sign in with Google
- [ ] Role selection works
- [ ] Doctor dashboard loads
- [ ] Can upload file for patient
- [ ] Patient dashboard loads
- [ ] Patient can see and download file
- [ ] File download works
- [ ] Backend health check responds (if enabled)

## Common Issues

**"Patient not found" error**:
- Patient must sign in first to create their profile
- Email must match exactly

**Firebase permission denied**:
- Deploy security rules: `firebase deploy --only firestore:rules,storage:rules`
- Check rules in Firebase Console

**Backend CORS error**:
- Add frontend URL to `ALLOWED_ORIGINS` in backend `.env`

**Tailwind styles not working**:
- Run `npm install` in frontend directory
- Restart dev server

## Next Steps

1. **Customize**: Update branding, colors, logos
2. **Add features**: Search, filters, pagination
3. **Deploy**: 
   - Frontend to Vercel/Firebase Hosting
   - Backend to Render/Railway
4. **Monitor**: Set up Firebase Analytics
5. **Secure**: Review and test security rules

## Need Help?

- Check `README.md` for detailed documentation
- Review Firebase Console for error logs
- Check browser console for frontend errors
- Check terminal for backend errors
