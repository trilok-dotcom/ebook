import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { collection, query, where, orderBy, getDocs, deleteDoc, doc, updateDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase';
import UploadForm from '../components/UploadForm';

export default function DoctorDashboard() {
  const { currentUser, userProfile, signOut } = useAuth();
  const [records, setRecords] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [activeTab, setActiveTab] = useState('records'); // records, appointments

  const loadRecords = async () => {
    setLoading(true);
    try {
      const q = query(
        collection(db, 'records'),
        where('uploadedBy', '==', currentUser.uid),
        orderBy('uploadedAt', 'desc')
      );
      const snapshot = await getDocs(q);
      const data = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));
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
        where('doctorId', '==', currentUser.uid),
        orderBy('createdAt', 'desc')
      );
      const snapshot = await getDocs(q);
      const data = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));
      setAppointments(data);
    } catch (error) {
      console.error('Error loading appointments:', error);
    }
  };

  const handleAppointmentAction = async (appointmentId, status) => {
    try {
      await updateDoc(doc(db, 'appointments', appointmentId), {
        status: status,
        updatedAt: serverTimestamp(),
      });
      alert(`Appointment ${status} successfully`);
      loadAppointments();
    } catch (error) {
      console.error('Error updating appointment:', error);
      alert('Failed to update appointment');
    }
  };

  const handleDelete = async (record) => {
    if (!confirm('Are you sure you want to delete this record?')) return;

    try {
      // Delete from Firestore (Cloudinary files remain accessible via URL)
      await deleteDoc(doc(db, 'records', record.id));

      alert('Record deleted successfully');
      loadRecords();
    } catch (error) {
      console.error('Error deleting record:', error);
      alert('Failed to delete record: ' + error.message);
    }
  };

  const filteredRecords =
    filterType === 'all'
      ? records
      : records.filter((r) => r.fileType === filterType);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Doctor Dashboard</h1>
            <p className="text-sm text-gray-600">Welcome, {userProfile?.displayName}</p>
          </div>
          <button
            onClick={signOut}
            className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
              Patient Records
            </button>
            <button
              onClick={() => setActiveTab('appointments')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'appointments'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Appointments
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
            <div className="mb-6 flex gap-4 items-center">
              <button
                onClick={() => setShowUploadForm(true)}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition"
              >
                Upload New Record
              </button>

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
                No records found. Upload your first record!
              </div>
            ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRecords.map((record) => (
                  <tr key={record.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {record.fileName}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {record.fileType}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.patientEmail}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.uploadedAt?.toDate?.()?.toLocaleDateString() || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <a
                        href={record.fileUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        View
                      </a>
                      <button
                        onClick={() => handleDelete(record)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
            )}
          </>
        )}

        {/* Appointments Tab */}
        {activeTab === 'appointments' && (
          <div className="space-y-4">
            {appointments.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No appointments yet.
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
                        {appointment.patientName}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {appointment.patientEmail}
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

                  <div className="space-y-2 text-sm text-gray-600 mb-4">
                    <p>
                      <strong>Date:</strong> {appointment.date} at {appointment.time}
                    </p>
                    {appointment.reason && (
                      <p>
                        <strong>Reason:</strong> {appointment.reason}
                      </p>
                    )}
                  </div>

                  {appointment.status === 'pending' && (
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleAppointmentAction(appointment.id, 'approved')}
                        className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleAppointmentAction(appointment.id, 'rejected')}
                        className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                      >
                        Reject
                      </button>
                    </div>
                  )}

                  {appointment.status === 'approved' && (
                    <button
                      onClick={() => handleAppointmentAction(appointment.id, 'completed')}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Mark as Completed
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </main>

      {/* Upload Modal */}
      {showUploadForm && (
        <UploadForm
          onClose={() => setShowUploadForm(false)}
          onSuccess={() => {
            setShowUploadForm(false);
            loadRecords();
          }}
        />
      )}
    </div>
  );
}
