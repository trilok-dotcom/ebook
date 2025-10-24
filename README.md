# Doctor-Patient Management System

A secure web application for managing medical records between doctors and patients using Firebase.

## Features

- **Google Authentication** via Firebase Auth
- **Role-based access**: Doctor or Patient
- **Doctor capabilities**:
  - Upload medical records (PDF, JPG, PNG)
  - Assign records to patients by email
  - View all uploaded records
  - Delete records (removes from both Storage and Firestore)
- **Patient capabilities**:
  - View all records assigned to them
  - Download records
  - Track viewed/downloaded status
- **Backend notifications** (optional):
  - Email via SendGrid
  - SMS via Twilio
  - Triggered when doctor uploads a record

## Tech Stack

### Frontend
- React 18 + Vite
- React Router v6
- Firebase SDK v10 (Auth, Firestore, Storage)
- Tailwind CSS
- React Hook Form
- React Query

### Backend (Optional)
- FastAPI
- Firebase Admin SDK
- SendGrid (email)
- Twilio (SMS)
- Uvicorn

## Project Structure

```
ebooklet/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── UploadForm.jsx
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Onboarding.jsx
│   │   │   ├── DoctorDashboard.jsx
│   │   │   └── PatientDashboard.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── firebase.js
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── schemas.py
│   │   └── notify.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── firestore.rules
├── storage.rules
└── README.md
```

## Setup Instructions

### Prerequisites

1. **Node.js** 18+ and npm
2. **Python** 3.10+ and pip
3. **Firebase Project**:
   - Create a project at [Firebase Console](https://console.firebase.google.com/)
   - Enable Google Authentication
   - Create Firestore database (production mode, then deploy rules)
   - Create Storage bucket
   - Generate service account key (for backend)

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   - Copy `.env.example` to `.env.local`
   - Fill in Firebase config from Firebase Console → Project Settings → General → Your apps → Web app:
     ```env
     VITE_FIREBASE_API_KEY=AIzaSy...
     VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
     VITE_FIREBASE_PROJECT_ID=your-project-id
     VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
     VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
     VITE_FIREBASE_APP_ID=1:123456789:web:abc123
     VITE_BACKEND_URL=http://localhost:8000
     ```

4. **Run development server**:
   ```bash
   npm run dev
   ```
   - Frontend runs at: http://localhost:5173

5. **Build for production**:
   ```bash
   npm run build
   ```

### Backend Setup (Optional - for notifications)

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Get Firebase service account:
     - Firebase Console → Project Settings → Service Accounts → Generate new private key
   - Fill in `.env`:
     ```env
     ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-domain.com
     FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
     FIREBASE_PROJECT_ID=your-project-id
     BASE_APP_URL=http://localhost:5173
     NOTIFY_CHANNELS=email
     SENDGRID_API_KEY=SG.xxx
     SENDGRID_FROM_EMAIL=notifications@yourdomain.com
     ```

5. **Run development server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - Backend runs at: http://localhost:8000
   - Health check: http://localhost:8000/api/healthz

### Firebase Security Rules Deployment

1. **Install Firebase CLI**:
   ```bash
   npm install -g firebase-tools
   ```

2. **Login to Firebase**:
   ```bash
   firebase login
   ```

3. **Initialize Firebase** (if not already):
   ```bash
   firebase init
   ```
   - Select Firestore and Storage
   - Use existing project
   - Point to `firestore.rules` and `storage.rules`

4. **Deploy rules**:
   ```bash
   firebase deploy --only firestore:rules
   firebase deploy --only storage:rules
   ```

## Usage Flow

### First-Time User

1. Visit the app and click "Sign in with Google"
2. After authentication, select role: **Doctor** or **Patient**
3. Optionally add phone number
4. Click "Continue" to create profile

### Doctor Workflow

1. Sign in → redirected to Doctor Dashboard
2. Click "Upload New Record"
3. Enter patient email (patient must be registered)
4. Select file type (report, prescription, other)
5. Add notes (optional)
6. Choose file (PDF, JPG, PNG)
7. Click "Upload"
8. Record appears in the list
9. (Optional) Backend sends notification to patient

### Patient Workflow

1. Sign in → redirected to Patient Dashboard
2. View all records uploaded for you
3. Click "View / Download" to open the file
4. Record is marked as "Viewed"

## Firebase Data Model

### Firestore Collections

#### `users/{uid}`
```json
{
  "uid": "firebase_user_id",
  "email": "user@example.com",
  "displayName": "John Doe",
  "role": "doctor" | "patient",
  "phone": "+1234567890",
  "createdAt": "Timestamp"
}
```

#### `records/{recordId}`
```json
{
  "fileUrl": "https://storage.googleapis.com/...",
  "storagePath": "records/doctorUid/patientUid/timestamp_filename.pdf",
  "fileName": "report.pdf",
  "fileType": "report" | "prescription" | "other",
  "uploadedBy": "doctor_uid",
  "uploadedFor": "patient_uid",
  "patientEmail": "patient@example.com",
  "notes": "Follow up in 2 weeks",
  "uploadedAt": "Timestamp",
  "acknowledged": false,
  "downloads": [
    {
      "uid": "patient_uid",
      "downloadedAt": "Timestamp"
    }
  ]
}
```

### Storage Structure

```
/records/{doctorUid}/{patientUid}/{timestamp}_{filename}
```

Example:
```
/records/abc123/xyz789/1698765432000_blood_test.pdf
```

## API Endpoints (Backend)

### GET `/api/healthz`
Health check endpoint.

**Response**:
```json
{
  "status": "ok"
}
```

### POST `/api/notify/upload`
Send notification to patient about new record.

**Headers**:
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Body**:
```json
{
  "recordId": "firestore_record_id"
}
```

**Response**:
```json
{
  "status": "sent",
  "channels": ["email"]
}
```

## Security

### Firestore Rules
- Users can only read/write their own user document
- Doctors can create records they upload
- Doctors and assigned patients can read records
- Only uploading doctor can update/delete records

### Storage Rules
- Files stored under `/records/{doctorUid}/{patientUid}/`
- Doctor can upload/delete files in their path
- Both doctor and patient can download files

### Backend Security
- All endpoints require Firebase ID token
- Token verified using Firebase Admin SDK
- Only record owner (doctor) can trigger notifications
- CORS restricted to allowed origins

## Deployment

### Frontend Deployment (Vercel)

1. **Push code to GitHub**

2. **Import to Vercel**:
   - Connect GitHub repository
   - Framework preset: Vite
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`

3. **Set environment variables** in Vercel dashboard:
   - All `VITE_FIREBASE_*` variables
   - `VITE_BACKEND_URL` (your backend URL)

4. **Deploy**

### Backend Deployment (Render)

1. **Create new Web Service** on Render

2. **Connect repository**

3. **Configure**:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

4. **Set environment variables**:
   - All variables from `.env`
   - Paste service account JSON as single line

5. **Deploy**

### Alternative: Firebase Hosting (Frontend)

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

## Testing

### Manual Testing Checklist

- [ ] Google Sign-In works
- [ ] Role selection creates user document
- [ ] Doctor can upload file for patient
- [ ] Patient sees uploaded file
- [ ] Patient can download file
- [ ] Download tracking works
- [ ] Doctor can delete record
- [ ] Unauthorized access blocked (try accessing other user's files)
- [ ] Backend notification sends (if enabled)

### Firebase Emulator (Local Testing)

1. **Install emulators**:
   ```bash
   firebase init emulators
   ```
   - Select Firestore, Storage, Auth

2. **Start emulators**:
   ```bash
   firebase emulators:start
   ```

3. **Update frontend** to use emulator (in `firebase.js`):
   ```javascript
   import { connectAuthEmulator } from 'firebase/auth';
   import { connectFirestoreEmulator } from 'firebase/firestore';
   import { connectStorageEmulator } from 'firebase/storage';
   
   if (import.meta.env.DEV) {
     connectAuthEmulator(auth, 'http://localhost:9099');
     connectFirestoreEmulator(db, 'localhost', 8080);
     connectStorageEmulator(storage, 'localhost', 9199);
   }
   ```

## Troubleshooting

### Frontend Issues

**Build errors about Tailwind**:
- Ensure `tailwind.config.js` and `postcss.config.js` exist
- Run `npm install -D tailwindcss postcss autoprefixer`

**Firebase errors**:
- Check `.env.local` has all required variables
- Verify Firebase project has Auth, Firestore, Storage enabled
- Check browser console for specific error messages

**Patient not found during upload**:
- Ensure patient has signed in at least once
- Email must match exactly (case-insensitive)
- Patient must have role="patient" in Firestore

### Backend Issues

**Import errors**:
- Activate virtual environment
- Run `pip install -r requirements.txt`

**Firebase Admin errors**:
- Verify service account JSON is valid
- Check `FIREBASE_PROJECT_ID` matches your project

**Notification not sending**:
- Check `NOTIFY_CHANNELS` is set
- Verify SendGrid/Twilio credentials
- Check patient has email/phone in profile

## Environment Variables Reference

### Frontend (.env.local)
```env
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_BACKEND_URL=
```

### Backend (.env)
```env
ALLOWED_ORIGINS=
FIREBASE_SERVICE_ACCOUNT_JSON=
FIREBASE_PROJECT_ID=
BASE_APP_URL=
NOTIFY_CHANNELS=
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
```

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
