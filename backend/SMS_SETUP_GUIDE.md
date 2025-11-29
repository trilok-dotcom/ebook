# SMS Notifications Setup Guide

## Overview
This guide will help you configure SMS notifications for appointment booking and approval in E-Booklet.

## Prerequisites
- Twilio account (free trial available)
- Phone number: **+918618898432** (already configured in test script)

## Step 1: Create Twilio Account

1. Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up for a free account
3. Verify your email and phone number
4. You'll get **$15 free credit** for testing

## Step 2: Get Twilio Credentials

After signing up, you'll need three pieces of information:

### 1. Account SID
- Go to [Twilio Console](https://console.twilio.com/)
- Find **Account SID** on the dashboard
- Example: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. Auth Token
- On the same dashboard page
- Click "Show" next to **Auth Token**
- Example: `your_auth_token_here`

### 3. Twilio Phone Number
- Click "Get a Trial Number" button
- Twilio will assign you a phone number
- Example: `+1234567890`

## Step 3: Configure Environment Variables

Edit your `.env` file in the `backend` folder:

```bash
# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890

# Enable SMS in notification channels
NOTIFY_CHANNELS=email,sms
```

**Important Notes:**
- Replace the example values with your actual Twilio credentials
- Keep the `TWILIO_AUTH_TOKEN` secret - never commit it to Git
- The `TWILIO_FROM_NUMBER` must include the country code (e.g., +1 for US)

## Step 4: Verify Phone Number (Trial Account Only)

If you're using a Twilio trial account:

1. Go to [Verified Caller IDs](https://console.twilio.com/us1/develop/phone-numbers/manage/verified)
2. Click "Add a new number"
3. Enter **+918618898432** (your phone number)
4. Verify via SMS or voice call
5. Once verified, you can receive SMS from your Twilio trial number

**Note:** Trial accounts can only send SMS to verified numbers. Upgrade to a paid account to send to any number.

## Step 5: Test SMS Notifications

### Test 1: Quick Test Script

```bash
cd backend
python test_notifications.py
```

This will:
- Check if the API is running
- Send a test SMS to +918618898432
- Display the results

### Test 2: Test via API

Start the backend server:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Then test with curl or Postman:

```bash
curl -X POST http://localhost:8000/api/notify/test \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "phone": "+918618898432"
  }'
```

## Step 6: Test Appointment Notifications

### Create an Appointment (with SMS)

```bash
curl -X POST http://localhost:8000/api/appointments/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -d '{
    "doctor_id": "doctor_uid",
    "doctor_name": "Dr. Smith",
    "patient_name": "Your Name",
    "patient_email": "your-email@example.com",
    "patient_phone": "+918618898432",
    "appointment_date": "2025-10-26",
    "appointment_time": "10:00 AM",
    "reason": "Regular checkup"
  }'
```

You should receive an SMS like:
```
Hi Your Name, Your appointment with Dr. Smith has been requested for 2025-10-26 at 10:00 AM. You will receive a confirmation once the doctor approves it. - E-Booklet
```

### Approve an Appointment (with SMS)

```bash
curl -X PUT http://localhost:8000/api/appointments/{appointment_id}/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer DOCTOR_FIREBASE_TOKEN" \
  -d '{
    "status": "approved",
    "notes": "Looking forward to seeing you!"
  }'
```

You should receive an SMS like:
```
Hi Your Name, Your appointment with Dr. Smith on 2025-10-26 at 10:00 AM has been approved! ✅

Note: Looking forward to seeing you! - E-Booklet
```

## Troubleshooting

### Issue 1: "SMS not configured" error

**Solution:** Check your `.env` file:
- Ensure all three Twilio variables are set
- Restart the backend server after changing `.env`
- Verify no extra spaces in the values

### Issue 2: "Phone number not verified" (Trial Account)

**Solution:**
- Go to Twilio Console → Verified Caller IDs
- Add and verify +918618898432
- Wait for verification to complete

### Issue 3: SMS not received

**Checklist:**
1. ✅ Twilio credentials are correct
2. ✅ Phone number is verified (for trial accounts)
3. ✅ Phone number includes country code (+91 for India)
4. ✅ Backend server is running
5. ✅ Check backend logs for errors
6. ✅ Check Twilio console logs: [Message Logs](https://console.twilio.com/us1/monitor/logs/sms)

### Issue 4: "Insufficient funds" error

**Solution:**
- Trial accounts get $15 credit
- Each SMS costs ~$0.0075
- Check your balance: [Twilio Console](https://console.twilio.com/)
- Add payment method if needed

## API Endpoints Summary

### 1. Test Notification
```
POST /api/notify/test
Body: { "email": "...", "phone": "+918618898432" }
Auth: None required
```

### 2. Book Appointment
```
POST /api/appointments/book
Body: { doctor_id, doctor_name, patient_name, patient_email, patient_phone, ... }
Auth: Required (Patient token)
SMS: Sent to patient_phone
```

### 3. Update Appointment Status
```
PUT /api/appointments/{appointment_id}/status
Body: { "status": "approved|rejected|cancelled|completed", "notes": "..." }
Auth: Required (Doctor token for approve/reject)
SMS: Sent to patient when status changes
```

## Cost Estimation

### Twilio Pricing (as of 2024)
- **SMS to India:** ~$0.0075 per message
- **Trial Credit:** $15 (≈2000 SMS messages)
- **Monthly Phone Number:** $1.15/month (after trial)

### Expected Usage
- Appointment booking: 1 SMS per booking
- Appointment approval: 1 SMS per approval
- Total: 2 SMS per appointment = ~$0.015 per appointment

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Rotate Auth Token** - If accidentally exposed
3. **Use environment variables** - Never hardcode credentials
4. **Monitor usage** - Set up billing alerts in Twilio
5. **Validate phone numbers** - Use proper format validation

## Support

### Twilio Support
- Documentation: [https://www.twilio.com/docs/sms](https://www.twilio.com/docs/sms)
- Support: [https://support.twilio.com](https://support.twilio.com)

### E-Booklet Support
- Check backend logs: `backend/logs/`
- Review `NOTIFICATIONS_SETUP.md` for email setup
- Test with `test_notifications.py` script

## Next Steps

1. ✅ Set up Twilio account
2. ✅ Configure `.env` file
3. ✅ Verify phone number (trial only)
4. ✅ Run test script
5. ✅ Test appointment booking
6. ✅ Test appointment approval
7. 🎉 SMS notifications are working!

---

**Your Phone Number:** +918618898432  
**Status:** Ready to receive SMS notifications
