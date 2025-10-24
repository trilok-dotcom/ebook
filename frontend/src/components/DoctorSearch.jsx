import { useState, useEffect } from 'react';
import { collection, query, where, getDocs } from 'firebase/firestore';
import { db } from '../firebase';
import { Search, Calendar, Phone, Mail } from 'lucide-react';

export default function DoctorSearch({ onBookAppointment }) {
  const [doctors, setDoctors] = useState([]);
  const [filteredDoctors, setFilteredDoctors] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDoctors();
  }, []);

  useEffect(() => {
    filterDoctors();
  }, [searchTerm, doctors]);

  const fetchDoctors = async () => {
    try {
      const usersRef = collection(db, 'users');
      const q = query(usersRef, where('role', '==', 'doctor'));
      const snapshot = await getDocs(q);
      
      const doctorsList = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      
      setDoctors(doctorsList);
      setFilteredDoctors(doctorsList);
    } catch (error) {
      console.error('Error fetching doctors:', error);
      alert('Failed to load doctors');
    } finally {
      setLoading(false);
    }
  };

  const filterDoctors = () => {
    if (!searchTerm.trim()) {
      setFilteredDoctors(doctors);
      return;
    }

    const term = searchTerm.toLowerCase();
    const filtered = doctors.filter(doctor => 
      doctor.displayName?.toLowerCase().includes(term) ||
      doctor.specialty?.toLowerCase().includes(term) ||
      doctor.email?.toLowerCase().includes(term)
    );
    
    setFilteredDoctors(filtered);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search by doctor name or specialty..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        {filteredDoctors.length} {filteredDoctors.length === 1 ? 'doctor' : 'doctors'} found
      </div>

      {/* Doctors List */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredDoctors.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            No doctors found matching your search.
          </div>
        ) : (
          filteredDoctors.map((doctor) => (
            <div
              key={doctor.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {doctor.displayName}
                  </h3>
                  <p className="text-sm text-blue-600 font-medium mt-1">
                    {doctor.specialty || 'General Physician'}
                  </p>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <Mail className="w-4 h-4 mr-2" />
                  <span className="truncate">{doctor.email}</span>
                </div>
                {doctor.phone && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="w-4 h-4 mr-2" />
                    <span>{doctor.phone}</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => onBookAppointment(doctor)}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Calendar className="w-4 h-4" />
                Book Appointment
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
