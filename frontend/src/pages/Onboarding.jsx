import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';
import { useAuth } from '../contexts/AuthContext';
import { db } from '../firebase';

const MEDICAL_SPECIALTIES = [
  'General Physician',
  'Cardiologist',
  'Dermatologist',
  'Pediatrician',
  'Orthopedic Surgeon',
  'Neurologist',
  'Psychiatrist',
  'Gynecologist',
  'Ophthalmologist',
  'ENT Specialist',
  'Dentist',
  'Radiologist',
  'Anesthesiologist',
  'Surgeon',
  'Urologist',
  'Gastroenterologist',
  'Endocrinologist',
  'Pulmonologist',
  'Nephrologist',
  'Oncologist',
  'Rheumatologist',
  'Allergist',
  'Pathologist',
  'Emergency Medicine',
  'Family Medicine',
];

export default function Onboarding() {
  const { currentUser, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState('');
  const [phone, setPhone] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSpecialties, setFilteredSpecialties] = useState([]);

  const handleSpecialtyChange = (value) => {
    setSpecialty(value);
    
    if (value.trim().length > 0) {
      const filtered = MEDICAL_SPECIALTIES.filter(spec =>
        spec.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredSpecialties(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setShowSuggestions(false);
      setFilteredSpecialties([]);
    }
  };

  const handleSelectSpecialty = (selectedSpecialty) => {
    setSpecialty(selectedSpecialty);
    setShowSuggestions(false);
    setFilteredSpecialties([]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!role) {
      alert('Please select a role');
      return;
    }

    if (role === 'doctor' && !specialty) {
      alert('Please enter your specialty');
      return;
    }

    setLoading(true);
    try {
      const userData = {
        uid: currentUser.uid,
        email: currentUser.email.toLowerCase().trim(),
        displayName: currentUser.displayName || currentUser.email,
        role: role,
        phone: phone || null,
        createdAt: serverTimestamp(),
      };

      // Add specialty for doctors
      if (role === 'doctor') {
        userData.specialty = specialty.trim();
      }

      await setDoc(doc(db, 'users', currentUser.uid), userData);

      await refreshProfile();
      navigate(`/${role}`);
    } catch (error) {
      console.error('Error creating profile:', error);
      alert('Failed to create profile: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Complete Your Profile
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              I am a:
            </label>
            <div className="space-y-3">
              <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition">
                <input
                  type="radio"
                  name="role"
                  value="doctor"
                  checked={role === 'doctor'}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-4 h-4 text-blue-600"
                />
                <div className="ml-3">
                  <div className="font-semibold text-gray-900">Doctor</div>
                  <div className="text-sm text-gray-500">
                    Upload and manage patient records
                  </div>
                </div>
              </label>

              <label className="flex items-center p-4 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition">
                <input
                  type="radio"
                  name="role"
                  value="patient"
                  checked={role === 'patient'}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-4 h-4 text-blue-600"
                />
                <div className="ml-3">
                  <div className="font-semibold text-gray-900">Patient</div>
                  <div className="text-sm text-gray-500">
                    View and download your medical records
                  </div>
                </div>
              </label>
            </div>
          </div>

          {role === 'doctor' && (
            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Specialty *
              </label>
              <input
                type="text"
                value={specialty}
                onChange={(e) => handleSpecialtyChange(e.target.value)}
                onFocus={() => {
                  if (specialty.trim().length > 0) {
                    const filtered = MEDICAL_SPECIALTIES.filter(spec =>
                      spec.toLowerCase().includes(specialty.toLowerCase())
                    );
                    setFilteredSpecialties(filtered);
                    setShowSuggestions(filtered.length > 0);
                  }
                }}
                onBlur={() => {
                  // Delay to allow click on suggestion
                  setTimeout(() => setShowSuggestions(false), 200);
                }}
                placeholder="Start typing... (e.g., Cardio, Derma)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={role === 'doctor'}
                autoComplete="off"
              />
              
              {/* Dropdown suggestions */}
              {showSuggestions && filteredSpecialties.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {filteredSpecialties.map((spec, index) => (
                    <div
                      key={index}
                      onClick={() => handleSelectSpecialty(spec)}
                      className="px-4 py-2 hover:bg-blue-50 cursor-pointer transition"
                    >
                      {spec}
                    </div>
                  ))}
                </div>
              )}
              
              <p className="text-xs text-gray-500 mt-1">
                This helps patients find the right doctor
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number (Optional)
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+1234567890"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !role || (role === 'doctor' && !specialty)}
            className="w-full bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition duration-200"
          >
            {loading ? 'Creating Profile...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
}
