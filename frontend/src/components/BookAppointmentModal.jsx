import { useState, useEffect } from 'react';
import { collection, addDoc, serverTimestamp, query, where, getDocs, doc, getDoc } from 'firebase/firestore';
import { db } from '../firebase';
import { useAuth } from '../contexts/AuthContext';
import { X, Calendar, Clock } from 'lucide-react';

export default function BookAppointmentModal({ doctor, onClose, onSuccess }) {
  const { currentUser } = useAuth();
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [bookedSlots, setBookedSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Generate time slots from 8:30 AM to 5:00 PM (30-minute intervals)
  const generateTimeSlots = () => {
    const slots = [];
    let hour = 8;
    let minute = 30;
    
    while (hour < 17 || (hour === 17 && minute === 0)) {
      const ampm = hour >= 12 ? 'PM' : 'AM';
      const displayHour = hour > 12 ? hour - 12 : hour;
      const timeString = `${displayHour}:${minute.toString().padStart(2, '0')} ${ampm}`;
      const valueString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
      
      slots.push({ display: timeString, value: valueString });
      
      // Increment by 30 minutes
      minute += 30;
      if (minute >= 60) {
        minute = 0;
        hour += 1;
      }
    }
    
    return slots;
  };

  const timeSlots = generateTimeSlots();

  // Fetch booked appointments when date is selected
  useEffect(() => {
    const fetchBookedSlots = async () => {
      if (!date || !doctor.id) return;
      
      setLoadingSlots(true);
      try {
        const q = query(
          collection(db, 'appointments'),
          where('doctorId', '==', doctor.id),
          where('date', '==', date),
          where('status', 'in', ['pending', 'approved']) // Only consider active appointments
        );
        
        const snapshot = await getDocs(q);
        const slots = snapshot.docs.map(doc => doc.data().time);
        setBookedSlots(slots);
        console.log('📅 Booked slots for', date, ':', slots);
      } catch (error) {
        console.error('Error fetching booked slots:', error);
        setBookedSlots([]);
      } finally {
        setLoadingSlots(false);
      }
    };

    fetchBookedSlots();
  }, [date, doctor.id]);

  // Check if a time slot is available
  const isSlotAvailable = (slotValue) => {
    return !bookedSlots.includes(slotValue);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!date || !time) {
      alert('Please select date and time');
      return;
    }

    // Double-check slot availability before booking (prevent race conditions)
    if (!isSlotAvailable(time)) {
      alert('Sorry, this time slot was just booked by another patient. Please select a different time.');
      return;
    }

    setLoading(true);
    try {
      // Final check: verify slot is still available
      const checkQuery = query(
        collection(db, 'appointments'),
        where('doctorId', '==', doctor.id),
        where('date', '==', date),
        where('time', '==', time),
        where('status', 'in', ['pending', 'approved'])
      );
      const checkSnapshot = await getDocs(checkQuery);
      
      if (!checkSnapshot.empty) {
        alert('Sorry, this time slot was just booked. Please select a different time.');
        setLoading(false);
        // Refresh booked slots
        const slots = checkSnapshot.docs.map(doc => doc.data().time);
        setBookedSlots(slots);
        setTime('');
        return;
      }

      await addDoc(collection(db, 'appointments'), {
        doctorId: doctor.id,
        doctorName: doctor.displayName,
        doctorSpecialty: doctor.specialty || 'General Physician',
        doctorEmail: doctor.email,
        patientId: currentUser.uid,
        patientName: currentUser.displayName || currentUser.email,
        patientEmail: currentUser.email,
        date: date,
        time: time,
        reason: reason || '',
        status: 'pending', // pending, approved, rejected, completed, cancelled
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      });

      // Send notification to patient
      try {
        const token = await currentUser.getIdToken();
        
        // Get patient phone from Firestore
        const userDocRef = doc(db, 'users', currentUser.uid);
        const userDocSnap = await getDoc(userDocRef);
        const userData = userDocSnap.exists() ? userDocSnap.data() : null;
        
        // Format date for notification
        const dateObj = new Date(date);
        const formattedDate = dateObj.toLocaleDateString('en-US', { 
          month: 'long', 
          day: 'numeric', 
          year: 'numeric' 
        });
        
        // Format time (convert 24h to 12h format)
        const [hours, minutes] = time.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const hour12 = hour % 12 || 12;
        const formattedTime = `${hour12}:${minutes} ${ampm}`;
        
        await fetch('http://localhost:8000/api/notify/appointment', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            patient_name: currentUser.displayName || currentUser.email,
            patient_email: currentUser.email,
            patient_phone: userData?.phone || null,
            doctor_name: doctor.displayName,
            appointment_date: formattedDate,
            appointment_time: formattedTime,
            appointment_reason: reason || null
          })
        });
        console.log('Appointment notification sent successfully!');
      } catch (notifError) {
        console.error('Failed to send notification:', notifError);
        // Don't fail the booking if notification fails
      }

      alert('Appointment request sent successfully!');
      onSuccess();
    } catch (error) {
      console.error('Error booking appointment:', error);
      alert('Failed to book appointment: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">Book Appointment</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Doctor Info */}
        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-gray-900">{doctor.displayName}</h3>
          <p className="text-sm text-blue-600">{doctor.specialty || 'General Physician'}</p>
          <p className="text-sm text-gray-600 mt-1">{doctor.email}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Calendar className="w-4 h-4 inline mr-1" />
              Appointment Date *
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              min={today}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Clock className="w-4 h-4 inline mr-1" />
              Preferred Time *
            </label>
            <select
              value={time}
              onChange={(e) => setTime(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              disabled={loading || loadingSlots || !date}
            >
              <option value="">
                {!date ? 'Please select a date first' : loadingSlots ? 'Loading available slots...' : 'Select a time slot'}
              </option>
              {timeSlots.map((slot) => {
                const available = isSlotAvailable(slot.value);
                return (
                  <option 
                    key={slot.value} 
                    value={slot.value}
                    disabled={!available}
                  >
                    {slot.display} {!available ? '(Booked)' : ''}
                  </option>
                );
              })}
            </select>
            {date && !loadingSlots && bookedSlots.length > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                {bookedSlots.length} slot{bookedSlots.length > 1 ? 's' : ''} already booked for this date
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason for Visit
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Describe your symptoms or reason for consultation..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Booking...' : 'Book Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
