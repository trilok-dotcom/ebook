import { useState } from 'react';
import { collection, addDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase';
import { useAuth } from '../contexts/AuthContext';
import { X, Calendar, Clock } from 'lucide-react';

export default function BookAppointmentModal({ doctor, onClose, onSuccess }) {
  const { currentUser } = useAuth();
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!date || !time) {
      alert('Please select date and time');
      return;
    }

    setLoading(true);
    try {
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
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
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
