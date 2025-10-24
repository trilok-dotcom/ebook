import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function ProtectedRoute({ children, requireRole }) {
  const { currentUser, userProfile, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (!currentUser) {
    return <Navigate to="/login" />;
  }

  if (!userProfile || !userProfile.role) {
    return <Navigate to="/onboarding" />;
  }

  if (requireRole && userProfile.role !== requireRole) {
    return <Navigate to={`/${userProfile.role}`} />;
  }

  return children;
}
