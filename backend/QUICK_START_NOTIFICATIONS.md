# ⚡ E-Booklet Notifications - Quick Start

## 🚀 5-Minute Setup

### Step 1: Get Gmail App Password (2 min)
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" → "Other" → Enter "E-Booklet"
3. Copy the 16-character password

### Step 2: Configure .env (1 min)
```env
# Add to backend/.env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # 16-char password from step 1
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=E-Booklet
EMAIL_PROVIDER=smtp
```

### Step 3: Test It! (2 min)
```bash
# Edit test_notifications.py - change email
TEST_EMAIL = "your_email@gmail.com"

# Run test
python test_notifications.py
```

✅ **Done!** Check your email inbox.

---

## 📧 Send Your First Notification

### Test Endpoint (No Auth):
```bash
curl -X POST http://localhost:8000/api/notify/test \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com"}'
```

### Appointment Notification:
```bash
curl -X POST http://localhost:8000/api/notify/appointment \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patient_name": "John Doe",
    "patient_email": "john@example.com",
    "doctor_name": "Dr. Smith",
    "appointment_date": "Oct 25, 2025",
    "appointment_time": "10:00 AM"
  }'
```

---

## 📱 Add SMS (Optional)

### Get Twilio Free Account:
1. Sign up at https://www.twilio.com/try-twilio ($15 free credit)
2. Get phone number
3. Copy Account SID & Auth Token

### Add to .env:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890
```

### Test SMS:
```bash
curl -X POST http://localhost:8000/api/notify/test \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "phone": "+1234567890"}'
```

---

## 🎯 API Endpoints

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /api/notify/test` | ❌ No | Test email/SMS |
| `POST /api/notify/appointment` | ✅ Yes | Appointment confirmation |
| `POST /api/notify/record` | ✅ Yes | Record upload alert |

---

## 🐛 Troubleshooting

**Email not sending?**
```bash
# Check logs
tail -f backend.log | grep "email"

# Common fixes:
# - Use App Password, not regular password
# - Enable 2FA on Google account first
# - Check SMTP_PORT=587 and SMTP_USE_TLS=true
```

**SMS not sending?**
```bash
# Check Twilio balance: https://console.twilio.com/
# Verify phone format: +1234567890 (with country code)
# Check logs for detailed error
```

---

## 📚 Full Documentation

- **Complete Guide:** `NOTIFICATIONS_SETUP.md`
- **Feature Summary:** `../NOTIFICATIONS_FEATURE_SUMMARY.md`
- **Postman Collection:** `E-Booklet_Notifications.postman_collection.json`

---

## ✨ That's It!

You're ready to send beautiful notifications! 🎉

**Next:** Integrate into your upload/appointment flows.
