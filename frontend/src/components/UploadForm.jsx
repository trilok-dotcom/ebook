import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { collection, query, where, getDocs, addDoc, serverTimestamp } from 'firebase/firestore';
import { db } from '../firebase';

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
      console.log('Starting upload process...');
      console.log('Current user:', currentUser.uid);
      
      // 1. Find patient by email
      const normalizedEmail = patientEmail.toLowerCase().trim();
      console.log('Looking for patient:', normalizedEmail);
      
      const usersRef = collection(db, 'users');
      const q = query(usersRef, where('email', '==', normalizedEmail));
      const snapshot = await getDocs(q);
      console.log('Patient query completed');

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

      // 2. Upload file to Cloudinary
      const formData = new FormData();
      formData.append('file', file);
      formData.append('upload_preset', 'medical_records');
      formData.append('folder', `records/${currentUser.uid}/${patientUid}`);

      // Upload to Cloudinary (using raw for documents, will work for images too)
      const cloudinaryUrl = `https://api.cloudinary.com/v1_1/${import.meta.env.VITE_CLOUDINARY_CLOUD_NAME}/raw/upload`;
      
      const xhr = new XMLHttpRequest();
      xhr.open('POST', cloudinaryUrl, true);
      
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100;
          setUploadProgress(progress);
        }
      };

      xhr.onload = async () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          const downloadURL = response.secure_url;
          const publicId = response.public_id;
          console.log('Cloudinary upload successful:', downloadURL);

          // 3. Create Firestore record
          console.log('Creating Firestore record...');
          console.log('uploadedBy:', currentUser.uid);
          console.log('uploadedFor:', patientUid);
          
          try {
            await addDoc(collection(db, 'records'), {
              fileUrl: downloadURL,
              cloudinaryPublicId: publicId,
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
            console.log('Firestore record created successfully!');

            // Send notification to patient
            try {
              const token = await currentUser.getIdToken();
              const doctorProfile = await getDocs(query(collection(db, 'users'), where('uid', '==', currentUser.uid)));
              const doctorData = doctorProfile.docs[0]?.data();
              
              await fetch('http://localhost:8000/api/notify/record', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                  patient_name: patientData.displayName || patientData.email,
                  patient_email: patientData.email,
                  patient_phone: patientData.phone || null,
                  doctor_name: doctorData?.displayName || currentUser.email,
                  record_name: file.name,
                  record_type: fileType.charAt(0).toUpperCase() + fileType.slice(1),
                  notes: notes || null
                })
              });
              console.log('Notification sent successfully!');
            } catch (notifError) {
              console.error('Failed to send notification:', notifError);
              // Don't fail the upload if notification fails
            }

            alert('Record uploaded successfully!');
            setUploading(false);
            onSuccess();
          } catch (firestoreError) {
            console.error('Firestore error:', firestoreError);
            alert('File uploaded but failed to save record: ' + firestoreError.message);
            setUploading(false);
          }
        } else {
          console.error('Upload error:', xhr.responseText);
          alert('Failed to upload file');
          setUploading(false);
        }
      };

      xhr.onerror = () => {
        console.error('Upload error');
        alert('Failed to upload file');
        setUploading(false);
      };

      xhr.send(formData);
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
