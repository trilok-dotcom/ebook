import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { collection, query, where, orderBy, getDocs, doc, updateDoc, arrayUnion, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase';

export default function PatientDashboard() {
  const { currentUser, userProfile, signOut } = useAuth();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('all');

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
  }, [currentUser]);

  const handleDownload = async (record) => {
    try {
      // Open file in new tab
      window.open(record.fileUrl, '_blank');

      // Track download
      const recordRef = doc(db, 'records', record.id);
      await updateDoc(recordRef, {
        downloads: arrayUnion({
          uid: currentUser.uid,
          downloadedAt: serverTimestamp(),
        }),
        acknowledged: true,
      });

      // Refresh records to show updated status
      loadRecords();
    } catch (error) {
      console.error('Error tracking download:', error);
      // Still allow download even if tracking fails
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
            <h1 className="text-2xl font-bold text-gray-900">Patient Dashboard</h1>
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
        {/* Filter */}
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

        {/* Records List */}
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
      </main>
    </div>
  );
}
