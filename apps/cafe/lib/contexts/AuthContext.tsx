'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User as FirebaseUser } from 'firebase/auth';
import { subscribeToAuthState, signOut as authSignOut } from '@/lib/firebase/auth';
import { getUser, subscribeToUser } from '@/lib/firebase/users';
import type { User, UserRole, ROLE_PERMISSIONS } from '@/lib/types';

interface AuthContextType {
  // State
  firebaseUser: FirebaseUser | null;
  user: User | null;
  loading: boolean;
  error: string | null;

  // Actions
  signOut: () => Promise<void>;

  // Helpers
  isAuthenticated: boolean;
  isEmailPasswordUser: boolean;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: UserRole | UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Permission mapping
const PERMISSIONS: Record<UserRole, string[]> = {
  gestor: ['admin', 'funcionários', 'produtos', 'caixa', 'pedidos', 'clientes'],
  gerente: ['caixa', 'pedidos', 'clientes'],
  barista: ['pedidos'],
};

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Subscribe to Firebase auth state
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    try {
      unsubscribe = subscribeToAuthState((fbUser) => {
        console.log('[AuthContext] Auth state changed:', fbUser?.email || 'null');
        setFirebaseUser(fbUser);

        if (!fbUser) {
          setUser(null);
          setLoading(false);
        }
      });
    } catch (err) {
      console.error('[AuthContext] Failed to subscribe to auth state:', err);
      setLoading(false);
      setError('Erro ao conectar com Firebase');
    }

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, []);

  // Subscribe to user data when Firebase user changes
  useEffect(() => {
    if (!firebaseUser) {
      setUser(null);
      return;
    }

    console.log('[AuthContext] Fetching user data for:', firebaseUser.uid);
    setLoading(true);

    let unsubscribe: (() => void) | null = null;

    try {
      unsubscribe = subscribeToUser(firebaseUser.uid, (userData) => {
        console.log('[AuthContext] User data received:', userData);
        if (userData && userData.active) {
          setUser(userData);
          setError(null);
        } else if (userData && !userData.active) {
          setUser(null);
          setError('Usuário desativado. Contate o administrador.');
          // Sign out inactive user
          authSignOut();
        } else {
          // User not found in database
          setUser(null);
          setError('Usuário não cadastrado no sistema.');
        }
        setLoading(false);
      });
    } catch (err) {
      console.error('[AuthContext] Error subscribing to user data:', err);
      setLoading(false);
      setError('Erro ao carregar dados do usuário');
    }

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [firebaseUser]);

  const signOut = async () => {
    try {
      await authSignOut();
      setUser(null);
      setFirebaseUser(null);
    } catch (err) {
      console.error('[AuthContext] Sign out error:', err);
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return PERMISSIONS[user.role]?.includes(permission) ?? false;
  };

  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    if (Array.isArray(role)) {
      return role.includes(user.role);
    }
    return user.role === role;
  };

  // Check if user logged in with email/password (not Google, etc.)
  const isEmailPasswordUser = (() => {
    if (!firebaseUser) return false;
    const providerData = firebaseUser.providerData;
    if (!providerData || providerData.length === 0) return false;
    return providerData[0]?.providerId === 'password';
  })();

  const value: AuthContextType = {
    firebaseUser,
    user,
    loading,
    error,
    signOut,
    isAuthenticated: !!user,
    isEmailPasswordUser,
    hasPermission,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
