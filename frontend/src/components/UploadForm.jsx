import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { collection, query, where, getDocs, addDoc, serverTimestamp } from 'firebase/firestore';
import { ref, uploadBytesResumable, getDownloadURL } from 'firebase/storage';
import { db, storage } from '../firebase';

export default function UploadForm({ onClose, onSuccess }) {
  const { currentUser } = useAuth();
  const [patientEmail, setPatientEmail] = useState('');
  const [fileType, setFileType] = useState('report');
  const [notes, setNotes] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      alert('Please select a file');
      return;
    }

    if (!patientEmail) {
      alert('Please enter patient email');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // 1. Find patient by email
      const normalizedEmail = patientEmail.toLowerCase().trim();
      const usersRef = collection(db, 'users');
      const q = query(usersRef, where('email', '==', normalizedEmail));
      const snapshot = await getDocs(q);

      if (snapshot.empty) {
        alert('Patient not found. Please ensure the email is correct and the patient has registered.');
        setUploading(false);
        return;
      }

      const patientDoc = snapshot.docs[0];
      const patientData = patientDoc.data();
      const patientUid = patientData.uid;

      if (patientData.role !== 'patient') {
        alert('The email provided is not registered as a patient.');
        setUploading(false);
        return;
      }

      // 2. Upload file to Storage
      const timestamp = Date.now();
      const storagePath = `records/${currentUser.uid}/${patientUid}/${timestamp}_${file.name}`;
      const storageRef = ref(storage, storagePath);
      const uploadTask = uploadBytesResumable(storageRef, file);

      uploadTask.on(
        'state_changed',
        (snapshot) => {
          const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
          setUploadProgress(progress);
        },
        (error) => {
          console.error('Upload error:', error);
          alert('Failed to upload file: ' + error.message);
          setUploading(false);
        },
        async () => {
          // 3. Get download URL
          const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);

          // 4. Create Firestore record
          await addDoc(collection(db, 'records'), {
            fileUrl: downloadURL,
            storagePath: storagePath,
            fileName: file.name,
            fileType: fileType,
            uploadedBy: currentUser.uid,
            uploadedFor: patientUid,
            patientEmail: normalizedEmail,
            notes: notes || '',
            uploadedAt: serverTimestamp(),
            acknowledged: false,
            downloads: [],
          });

          // 5. Optional: Call backend to notify patient
          try {
            const backendUrl = import.meta.env.VITE_BACKEND_URL;
            if (backendUrl) {
              const idToken = await currentUser.getIdToken();
              // Note: recordId would need to be returned from addDoc above
              // For simplicity, skipping notification call here
              // You can enhance this by getting the doc ID and calling backend
            }
          } catch (notifyError) {
            console.warn('Notification failed:', notifyError);
          }

          alert('Record uploaded successfully!');
          onSuccess();
        }
      );
    } catch (error) {
      console.error('Error uploading record:', error);
      alert('Failed to upload record: ' + error.message);
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">Upload Medical Record</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={uploading}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Patient Email *
            </label>
            <input
              type="email"
              value={patientEmail}
              onChange={(e) => setPatientEmail(e.target.value)}
              required
              placeholder="patient@example.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              File Type *
            </label>
            <select
              value={fileType}
              onChange={(e) => setFileType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            >
              <option value="report">Report</option>
              <option value="prescription">Prescription</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Additional notes for the patient..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              File (PDF, JPG, PNG) *
            </label>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={(e) => setFile(e.target.files[0])}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            />
          </div>

          {uploading && (
            <div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-1 text-center">
                Uploading... {Math.round(uploadProgress)}%
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
