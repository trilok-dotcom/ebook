# 📧 E-Booklet Notifications Service

Complete guide to set up and use the notifications service for sending beautiful email and SMS notifications to patients and doctors.

## 🎯 Features

- ✅ **Email Notifications** via Gmail SMTP or SendGrid
- ✅ **SMS Notifications** via Twilio
- ✅ **Beautiful HTML Email Templates** with modern design
- ✅ **Appointment Confirmations**
- ✅ **Record Upload Notifications**
- ✅ **Graceful Error Handling**
- ✅ **Async/Await Support**

---

## 📁 Directory Structure

```
backend/
├── app/
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── service.py              # Main notification service
│   │   ├── providers.py            # Email & SMS providers
│   │   └── templates/
│   │       ├── appointment_confirmation.html
│   │       ├── record_uploaded.html
│   │       └── general_notification.html
│   ├── routes/
│   │   ├── __init__.py
│   │   └── notifications.py        # API endpoints
│   └── main.py
└── .env
```

---

## ⚙️ Setup Instructions

### 1. Install Dependencies

Already included in `requirements.txt`:
```bash
pip install fastapi uvicorn firebase-admin sendgrid twilio tenacity slowapi pydantic-settings
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

#### **For Gmail (Recommended for testing):**

```env
# Email via Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=E-Booklet

EMAIL_PROVIDER=smtp
```

**How to get Gmail App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "E-Booklet" as the name
4. Copy the 16-character password
5. Paste it in `SMTP_PASSWORD`

#### **For Twilio SMS:**

```env
# SMS via Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890
```

**How to get Twilio credentials:**
1. Sign up at https://www.twilio.com/try-twilio
2. Get $15 free credit
3. Go to Console → Account Info
4. Copy Account SID and Auth Token
5. Get a phone number from Phone Numbers → Manage → Buy a number

#### **Enable/Disable Notifications:**

```env
NOTIFY_CHANNELS=email,sms  # or just "email" or "sms"
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_SMS_NOTIFICATIONS=true
```

---

## 🚀 API Endpoints

### 1. **Send Appointment Notification**

**Endpoint:** `POST /api/notify/appointment`

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "patient_name": "John Doe",
  "patient_email": "john@example.com",
  "patient_phone": "+1234567890",
  "doctor_name": "Dr. Sarah Smith",
  "appointment_date": "October 25, 2025",
  "appointment_time": "10:00 AM",
  "appointment_reason": "Annual Checkup"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Appointment notification sent successfully",
  "email": {
    "success": true,
    "message": "Email sent successfully"
  },
  "sms": {
    "success": true,
    "message": "SMS sent successfully"
  }
}
```

---

### 2. **Send Record Upload Notification**

**Endpoint:** `POST /api/notify/record`

**Headers:**
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "patient_name": "John Doe",
  "patient_email": "john@example.com",
  "patient_phone": "+1234567890",
  "doctor_name": "Dr. Sarah Smith",
  "record_name": "Blood Test Results",
  "record_type": "Lab Report",
  "notes": "All values are within normal range"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Record notification sent successfully",
  "email": {
    "success": true,
    "message": "Email sent successfully"
  },
  "sms": {
    "success": true,
    "message": "SMS sent successfully"
  }
}
```

---

### 3. **Test Notification (No Auth Required)**

**Endpoint:** `POST /api/notify/test`

**Request Body:**
```json
{
  "email": "test@example.com",
  "phone": "+1234567890"
}
```

---

## 🧪 Testing with cURL

### Test Email Only:
```bash
curl -X POST http://localhost:8000/api/notify/test \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@gmail.com"
  }'
```

### Test Email + SMS:
```bash
curl -X POST http://localhost:8000/api/notify/test \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@gmail.com",
    "phone": "+1234567890"
  }'
```

### Send Appointment Notification:
```bash
curl -X POST http://localhost:8000/api/notify/appointment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -d '{
    "patient_name": "John Doe",
    "patient_email": "john@example.com",
    "patient_phone": "+1234567890",
    "doctor_name": "Dr. Sarah Smith",
    "appointment_date": "October 25, 2025",
    "appointment_time": "10:00 AM",
    "appointment_reason": "Annual Checkup"
  }'
```

---

## 🎨 Email Templates

### Appointment Confirmation Email
- **Subject:** "Your Appointment is Confirmed 🩺"
- **Design:** Purple gradient header, appointment card with icons
- **Includes:** Doctor name, date, time, reason, dashboard link

### Record Upload Email
- **Subject:** "New Health Record Uploaded 📄"
- **Design:** Blue gradient header, record card with details
- **Includes:** Record name, type, doctor, upload date, notes

### General Notification Email
- **Subject:** Custom
- **Design:** Green gradient header, flexible content
- **Includes:** Custom message, optional CTA button

---

## 📱 SMS Templates

### Appointment Confirmation:
```
Hi John, your appointment with Dr. Sarah Smith on Oct 25, 10:00 AM is confirmed. - E-Booklet
```

### Record Upload:
```
Hi John, a new health record "Blood Test Results" has been added to your profile. Check your app. - E-Booklet
```

---

## 🔧 Troubleshooting

### Email not sending?

1. **Check Gmail App Password:**
   - Make sure you're using an App Password, not your regular password
   - Enable 2FA on your Google account first

2. **Check SMTP settings:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USE_TLS=true
   ```

3. **Check logs:**
   ```bash
   # Backend logs will show detailed error messages
   python -m uvicorn app.main:app --reload --port 8000
   ```

### SMS not sending?

1. **Verify Twilio credentials:**
   - Account SID starts with "AC"
   - Auth Token is correct
   - Phone number includes country code (+1)

2. **Check Twilio balance:**
   - Go to https://console.twilio.com/
   - Ensure you have credit

3. **Verify phone number format:**
   - Must include country code: `+1234567890`
   - No spaces or dashes

### Common Errors:

**"SMTP authentication failed"**
- Use App Password, not regular password
- Enable "Less secure app access" (not recommended) OR use App Password

**"Twilio authentication failed"**
- Double-check Account SID and Auth Token
- Ensure no extra spaces in .env file

**"Template not found"**
- Ensure templates are in `app/notifications/templates/`
- Check file names match exactly

---

## 🎯 Integration Example

### In your upload record function:

```python
from app.routes.notifications import send_record_notification

# After uploading record to Cloudinary and Firestore
notification_data = {
    "patient_name": patient_data["displayName"],
    "patient_email": patient_data["email"],
    "patient_phone": patient_data.get("phone"),
    "doctor_name": doctor_profile["displayName"],
    "record_name": file.filename,
    "record_type": record_type,
    "notes": notes
}

# Send notification
await send_record_notification(notification_data, user_id=current_user.uid)
```

---

## 📊 Monitoring

Check notification status in logs:
```bash
tail -f backend.log | grep "notification"
```

---

## 🚀 Production Deployment

### For production, consider:

1. **Use SendGrid instead of Gmail:**
   - More reliable for high volume
   - Better deliverability
   - Professional sender reputation

2. **Set up proper DNS records:**
   - SPF, DKIM, DMARC for email authentication

3. **Monitor delivery rates:**
   - Track bounces and complaints
   - Implement retry logic (already included)

4. **Use environment-specific templates:**
   - Different URLs for dev/staging/prod

---

## 📝 License

© 2025 E-Booklet - Secure Medical Records Management

---

## 🆘 Support

For issues or questions:
1. Check logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test with the `/api/notify/test` endpoint first
4. Check Twilio/Gmail console for delivery status
