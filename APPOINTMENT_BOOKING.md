# 📅 Appointment Booking with Time Slot Validation

## ✅ Features Implemented

### 🎯 Core Functionality:
- ✅ **Time Slot Validation** - Prevents double-booking
- ✅ **Conflict Detection** - Checks for overlapping appointments
- ✅ **Available Slots API** - Shows all available time slots for a doctor
- ✅ **Booking API** - Books appointments with validation
- ✅ **My Appointments** - Get all appointments for current user

---

## 🚀 API Endpoints

### 1. **Check Time Slot Availability**

**Endpoint:** `POST /api/appointments/check-availability`

**Purpose:** Check if a specific time slot is available before booking

**Request:**
```json
{
  "doctor_id": "doctor_firebase_uid",
  "appointment_date": "2025-10-25",
  "appointment_time": "10:00 AM"
}
```

**Response (Available):**
```json
{
  "available": true,
  "message": "Time slot is available"
}
```

**Response (Not Available):**
```json
{
  "available": false,
  "message": "This time slot is already booked",
  "conflicts": [
    {
      "appointment_id": "abc123",
      "patient_name": "John Doe",
      "time": "10:00 AM",
      "status": "pending"
    }
  ]
}
```

---

### 2. **Book Appointment (with validation)**

**Endpoint:** `POST /api/appointments/book`

**Purpose:** Book an appointment with automatic time slot validation

**Request:**
```json
{
  "doctor_id": "doctor_firebase_uid",
  "doctor_name": "Dr. Sarah Smith",
  "patient_name": "John Doe",
  "patient_email": "john@example.com",
  "patient_phone": "+1234567890",
  "appointment_date": "2025-10-25",
  "appointment_time": "10:00 AM",
  "reason": "Annual Checkup"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Appointment booked successfully",
  "appointment_id": "xyz789",
  "appointment": {
    "doctorId": "doctor_firebase_uid",
    "doctorName": "Dr. Sarah Smith",
    "patientId": "patient_firebase_uid",
    "patientName": "John Doe",
    "date": "2025-10-25",
    "time": "10:00 AM",
    "status": "pending",
    "id": "xyz789"
  }
}
```

**Response (Conflict - 409):**
```json
{
  "detail": {
    "error": "Time slot not available",
    "message": "This time slot is already booked. Please choose another time.",
    "conflicts": [
      {
        "appointment_id": "abc123",
        "patient_name": "Jane Smith",
        "time": "10:00 AM",
        "status": "approved"
      }
    ]
  }
}
```

---

### 3. **Get Available Slots**

**Endpoint:** `GET /api/appointments/available-slots/{doctor_id}?date=2025-10-25`

**Purpose:** Get all available time slots for a doctor on a specific date

**Response:**
```json
{
  "date": "2025-10-25",
  "doctor_id": "doctor_firebase_uid",
  "total_slots": 16,
  "available_slots": 12,
  "slots": [
    {
      "time": "09:00 AM",
      "available": true
    },
    {
      "time": "09:30 AM",
      "available": true
    },
    {
      "time": "10:00 AM",
      "available": false,
      "appointment_id": "abc123",
      "status": "approved"
    },
    {
      "time": "10:30 AM",
      "available": true
    }
    // ... more slots
  ]
}
```

**Working Hours:** 9:00 AM - 5:00 PM  
**Slot Duration:** 30 minutes

---

### 4. **Get My Appointments**

**Endpoint:** `GET /api/appointments/my-appointments`

**Purpose:** Get all appointments for the current user (patient or doctor)

**Response:**
```json
{
  "appointments": [
    {
      "id": "xyz789",
      "doctorId": "doctor_uid",
      "doctorName": "Dr. Sarah Smith",
      "patientId": "patient_uid",
      "patientName": "John Doe",
      "patientEmail": "john@example.com",
      "date": "2025-10-25",
      "time": "10:00 AM",
      "reason": "Annual Checkup",
      "status": "pending",
      "createdAt": "..."
    }
  ],
  "total": 1
}
```

---

## 🔒 How Time Slot Validation Works

### 1. **Conflict Detection Algorithm:**

```python
# Each appointment has a 30-minute duration
slot1_start = 10:00 AM
slot1_end = 10:30 AM

slot2_start = 10:15 AM  # Trying to book
slot2_end = 10:45 AM

# Check for overlap:
if (slot1_start < slot2_end) AND (slot2_start < slot1_end):
    # CONFLICT! Slots overlap
```

### 2. **Validation Flow:**

```
Patient tries to book → Check availability → 
  ├─ Available? → Book appointment → Success ✅
  └─ Not available? → Return conflict error → Show alternative slots ❌
```

### 3. **Edge Cases Handled:**

- ✅ Cancelled appointments don't block slots
- ✅ Rejected appointments don't block slots
- ✅ 30-minute buffer between appointments
- ✅ Multiple date formats supported
- ✅ Invalid date/time formats are handled gracefully

---

## 🎨 Frontend Integration Example

### Check Availability Before Showing Booking Form:

```javascript
// When user selects a time slot
const checkAvailability = async (doctorId, date, time) => {
  try {
    const response = await fetch('/api/appointments/check-availability', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${firebaseToken}`
      },
      body: JSON.stringify({
        doctor_id: doctorId,
        appointment_date: date,
        appointment_time: time
      })
    });
    
    const result = await response.json();
    
    if (result.available) {
      // Show booking form
      showBookingForm();
    } else {
      // Show error and suggest alternative times
      alert('This slot is already booked. Please choose another time.');
      showAlternativeSlots();
    }
  } catch (error) {
    console.error('Error checking availability:', error);
  }
};
```

### Book Appointment:

```javascript
const bookAppointment = async (appointmentData) => {
  try {
    const response = await fetch('/api/appointments/book', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${firebaseToken}`
      },
      body: JSON.stringify(appointmentData)
    });
    
    if (response.status === 409) {
      // Time slot conflict
      const error = await response.json();
      alert(error.detail.message);
      // Show alternative slots
      return;
    }
    
    if (response.ok) {
      const result = await response.json();
      alert('Appointment booked successfully!');
      // Redirect to appointments page
      navigate('/patient/appointments');
    }
  } catch (error) {
    console.error('Error booking appointment:', error);
  }
};
```

### Show Available Slots:

```javascript
const loadAvailableSlots = async (doctorId, date) => {
  try {
    const response = await fetch(
      `/api/appointments/available-slots/${doctorId}?date=${date}`,
      {
        headers: {
          'Authorization': `Bearer ${firebaseToken}`
        }
      }
    );
    
    const result = await response.json();
    
    // Display slots
    result.slots.forEach(slot => {
      if (slot.available) {
        // Show as clickable/selectable
        renderAvailableSlot(slot.time);
      } else {
        // Show as disabled/booked
        renderBookedSlot(slot.time);
      }
    });
  } catch (error) {
    console.error('Error loading slots:', error);
  }
};
```

---

## 🧪 Testing

### Test 1: Book First Appointment (Should Succeed)
```bash
curl -X POST http://localhost:8000/api/appointments/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "doctor_id": "doctor123",
    "doctor_name": "Dr. Smith",
    "patient_name": "John Doe",
    "patient_email": "john@example.com",
    "appointment_date": "2025-10-25",
    "appointment_time": "10:00 AM",
    "reason": "Checkup"
  }'
```

### Test 2: Try to Book Same Slot (Should Fail with 409)
```bash
curl -X POST http://localhost:8000/api/appointments/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ANOTHER_USER_TOKEN" \
  -d '{
    "doctor_id": "doctor123",
    "doctor_name": "Dr. Smith",
    "patient_name": "Jane Doe",
    "patient_email": "jane@example.com",
    "appointment_date": "2025-10-25",
    "appointment_time": "10:00 AM",
    "reason": "Consultation"
  }'
```

Expected: **409 Conflict** with message about slot being booked

### Test 3: Check Available Slots
```bash
curl -X GET "http://localhost:8000/api/appointments/available-slots/doctor123?date=2025-10-25" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📊 Database Structure

### Firestore Collection: `appointments`

```javascript
{
  "doctorId": "firebase_uid",
  "doctorName": "Dr. Sarah Smith",
  "patientId": "firebase_uid",
  "patientName": "John Doe",
  "patientEmail": "john@example.com",
  "patientPhone": "+1234567890",
  "date": "2025-10-25",  // or "October 25, 2025"
  "time": "10:00 AM",
  "reason": "Annual Checkup",
  "status": "pending",  // pending, approved, rejected, cancelled, completed
  "createdAt": Timestamp,
  "updatedAt": Timestamp
}
```

---

## 🎯 Status Workflow

```
pending → approved → completed
   ↓
rejected

cancelled (can be done by patient at any time)
```

- **pending**: Waiting for doctor approval
- **approved**: Doctor approved, appointment confirmed
- **rejected**: Doctor rejected the appointment
- **cancelled**: Patient cancelled the appointment
- **completed**: Appointment finished

---

## ⚙️ Configuration

### Appointment Settings (Customizable):

```python
# In app/routes/appointments.py

# Working hours
working_hours_start = 9   # 9 AM
working_hours_end = 17    # 5 PM

# Slot duration
slot_duration = 30  # minutes

# You can modify these based on doctor preferences
```

---

## 🔧 Future Enhancements

- [ ] Doctor-specific working hours
- [ ] Different slot durations per doctor
- [ ] Recurring appointments
- [ ] Appointment reminders (24h before)
- [ ] Waiting list for cancelled slots
- [ ] Video call integration
- [ ] Calendar sync (Google Calendar, Outlook)

---

## 🐛 Troubleshooting

### "Time slot not available" but no appointments exist?

**Check:**
1. Appointment status (cancelled/rejected appointments don't block)
2. Date format consistency
3. Time zone issues

### Slots showing as booked when they shouldn't be?

**Check:**
1. Firestore query filters
2. Status field values
3. Date parsing logic

### Multiple bookings for same slot?

**Check:**
1. Ensure validation is called before booking
2. Check for race conditions (use Firestore transactions if needed)

---

## ✨ Summary

✅ **Time slot validation prevents double-booking**  
✅ **Conflict detection with 30-minute slots**  
✅ **Available slots API for easy UI integration**  
✅ **Comprehensive error handling**  
✅ **Works with existing appointment system**

**Ready to use!** 🚀

---

© 2025 E-Booklet | Secure Medical Records Management
