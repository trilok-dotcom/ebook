import { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, signInWithPopup, signOut as firebaseSignOut } from 'firebase/auth';
import { doc, getDoc } from 'firebase/firestore';
import { auth, googleProvider, db } from '../firebase';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      console.log('Auth state changed:', user ? user.uid : 'no user');
      
      if (user) {
        try {
          // Fetch user profile from Firestore
          console.log('Fetching profile for user:', user.uid);
          const userDocRef = doc(db, 'users', user.uid);
          const userDoc = await getDoc(userDocRef);
          
          console.log('Document exists:', userDoc.exists());
          
          if (userDoc.exists()) {
            const profileData = userDoc.data();
            console.log('Profile data loaded:', JSON.stringify(profileData, null, 2));
            console.log('Role:', profileData.role);
            
            // Set both user and profile together
            setCurrentUser(user);
            setUserProfile(profileData);
          } else {
            console.log('❌ No profile document found, user needs onboarding');
            setCurrentUser(user);
            setUserProfile(null);
          }
        } catch (error) {
          console.error('❌ Error fetching user profile:', error);
          console.error('Error details:', error.code, error.message);
          setCurrentUser(user);
          setUserProfile(null);
        }
      } else {
        console.log('No user signed in');
        setCurrentUser(null);
        setUserProfile(null);
      }
      
      setLoading(false);
      console.log('Loading complete');
    });

    return unsubscribe;
  }, []);

  const signInWithGoogle = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (error) {
      console.error('Error signing in with Google:', error);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      await firebaseSignOut(auth);
      setUserProfile(null);
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  };

  const refreshProfile = async () => {
    if (currentUser) {
      const userDoc = await getDoc(doc(db, 'users', currentUser.uid));
      if (userDoc.exists()) {
        setUserProfile(userDoc.data());
      }
    }
  };

  const value = {
    currentUser,
    userProfile,
    signInWithGoogle,
    signOut,
    refreshProfile,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
