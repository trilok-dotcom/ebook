import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { collection, query, where, orderBy, getDocs, doc, updateDoc, arrayUnion, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase';
import DoctorSearch from '../components/DoctorSearch';
import BookAppointmentModal from '../components/BookAppointmentModal';

export default function PatientDashboard() {
  const { currentUser, userProfile, signOut } = useAuth();
  const [records, setRecords] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [activeTab, setActiveTab] = useState('records'); // records, doctors, appointments
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [showBookingModal, setShowBookingModal] = useState(false);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const q = query(
        collection(db, 'records'),
        where('uploadedFor', '==', currentUser.uid),
        orderBy('uploadedAt', 'desc')
      );
      const snapshot = await getDocs(q);
      const data = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));
      console.log('📚 Loaded records:', data.length, 'Unread:', data.filter(r => !r.acknowledged).length);
      setRecords(data);
    } catch (error) {
      console.error('Error loading records:', error);
      alert('Failed to load records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
    loadAppointments();
  }, [currentUser]);

  const loadAppointments = async () => {
    try {
      const q = query(
        collection(db, 'appointments'),
        where('patientId', '==', currentUser.uid),
        orderBy('createdAt', 'desc')
      );
      const snapshot = await getDocs(q);
      const data = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));
      setAppointments(data);
    } catch (error) {
      console.error('Error loading appointments:', error);
    }
  };

  const handleBookAppointment = (doctor) => {
    setSelectedDoctor(doctor);
    setShowBookingModal(true);
  };

  const handleBookingSuccess = () => {
    setShowBookingModal(false);
    setSelectedDoctor(null);
    loadAppointments();
    setActiveTab('appointments');
  };

  const handleDownload = async (record) => {
    try {
      console.log('📥 Viewing record:', record.id, 'Current acknowledged:', record.acknowledged);
      
      // Open file in new tab
      window.open(record.fileUrl, '_blank');

      // Track download
      const recordRef = doc(db, 'records', record.id);
      await updateDoc(recordRef, {
        downloads: arrayUnion({
          uid: currentUser.uid,
          downloadedAt: new Date().toISOString(),
        }),
        acknowledged: true,
      });

      console.log('✅ Firestore updated, now updating local state');
      
      // Update local state immediately to reflect the change
      setRecords(prevRecords => {
        const updated = prevRecords.map(r => 
          r.id === record.id ? { ...r, acknowledged: true } : r
        );
        console.log('📊 Unread count after update:', updated.filter(r => !r.acknowledged).length);
        return updated;
      });
    } catch (error) {
      console.error('❌ Error tracking download:', error);
      // Still allow download even if tracking fails
    }
  };

  const filteredRecords =
    filterType === 'all'
      ? records
      : records.filter((r) => r.fileType === filterType);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">E-Booklet</h1>
              <p className="text-sm text-gray-600 mt-1">🧑‍💼 {userProfile?.displayName}</p>
            </div>
            <button
              onClick={signOut}
              className="px-6 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-red-500 to-red-600 rounded-lg hover:from-red-600 hover:to-red-700 transition-all shadow-md hover:shadow-lg"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">My Records</p>
                <p className="text-3xl font-bold text-purple-600 mt-2">{records.length}</p>
              </div>
              <div className="bg-purple-100 p-4 rounded-full">
                <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Appointments</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">{appointments.length}</p>
              </div>
              <div className="bg-blue-100 p-4 rounded-full">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Unread Records</p>
                <p className="text-3xl font-bold text-pink-600 mt-2">{records.filter(r => !r.acknowledged).length}</p>
              </div>
              <div className="bg-pink-100 p-4 rounded-full">
                <svg className="w-8 h-8 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('records')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'records'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              My Records
            </button>
            <button
              onClick={() => setActiveTab('doctors')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'doctors'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Find Doctors
            </button>
            <button
              onClick={() => setActiveTab('appointments')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'appointments'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              My Appointments
              {appointments.filter(a => a.status === 'pending').length > 0 && (
                <span className="ml-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                  {appointments.filter(a => a.status === 'pending').length}
                </span>
              )}
            </button>
          </nav>
        </div>
        {/* Records Tab */}
        {activeTab === 'records' && (
          <>
            <div className="mb-6">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="report">Reports</option>
                <option value="prescription">Prescriptions</option>
                <option value="other">Other</option>
              </select>
            </div>

            {loading ? (
              <div className="text-center py-12">Loading records...</div>
            ) : filteredRecords.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No records found. Your doctor will upload records for you.
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredRecords.map((record) => (
                  <div
                    key={record.id}
                    className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {record.fileName}
                        </h3>
                        <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          {record.fileType}
                        </span>
                      </div>
                      {record.acknowledged && (
                        <span className="text-green-500 text-sm">✓ Viewed</span>
                      )}
                    </div>

                    {record.notes && (
                      <p className="text-sm text-gray-600 mb-4">{record.notes}</p>
                    )}

                    <div className="text-xs text-gray-500 mb-4">
                      Uploaded: {record.uploadedAt?.toDate?.()?.toLocaleDateString() || 'N/A'}
                    </div>

                    <button
                      onClick={() => handleDownload(record)}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    >
                      View / Download
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Doctors Tab */}
        {activeTab === 'doctors' && (
          <DoctorSearch onBookAppointment={handleBookAppointment} />
        )}

        {/* Appointments Tab */}
        {activeTab === 'appointments' && (
          <div className="space-y-4">
            {appointments.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No appointments yet. Search for doctors to book an appointment.
              </div>
            ) : (
              appointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="bg-white rounded-lg shadow p-6"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        Dr. {appointment.doctorName}
                      </h3>
                      <p className="text-sm text-blue-600">
                        {appointment.doctorSpecialty}
                      </p>
                    </div>
                    <span
                      className={`px-3 py-1 text-xs font-semibold rounded-full ${
                        appointment.status === 'approved'
                          ? 'bg-green-100 text-green-800'
                          : appointment.status === 'rejected'
                          ? 'bg-red-100 text-red-800'
                          : appointment.status === 'completed'
                          ? 'bg-gray-100 text-gray-800'
                          : appointment.status === 'cancelled'
                          ? 'bg-gray-100 text-gray-600'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                    </span>
                  </div>

                  <div className="space-y-2 text-sm text-gray-600">
                    <p>
                      <strong>Date:</strong> {appointment.date} at {appointment.time}
                    </p>
                    {appointment.reason && (
                      <p>
                        <strong>Reason:</strong> {appointment.reason}
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Booking Modal */}
        {showBookingModal && selectedDoctor && (
          <BookAppointmentModal
            doctor={selectedDoctor}
            onClose={() => {
              setShowBookingModal(false);
              setSelectedDoctor(null);
            }}
            onSuccess={handleBookingSuccess}
          />
        )}
      </main>
    </div>
  );
}
