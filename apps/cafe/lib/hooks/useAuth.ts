'use client';

import { useState } from 'react';
import { useAuthContext } from '@/lib/contexts/AuthContext';
import { signInWithEmail, signInWithGoogle, AuthResult } from '@/lib/firebase/auth';

export interface UseAuthReturn {
  // From context
  user: ReturnType<typeof useAuthContext>['user'];
  firebaseUser: ReturnType<typeof useAuthContext>['firebaseUser'];
  loading: ReturnType<typeof useAuthContext>['loading'];
  isAuthenticated: ReturnType<typeof useAuthContext>['isAuthenticated'];
  isEmailPasswordUser: ReturnType<typeof useAuthContext>['isEmailPasswordUser'];
  hasPermission: ReturnType<typeof useAuthContext>['hasPermission'];
  hasRole: ReturnType<typeof useAuthContext>['hasRole'];
  signOut: ReturnType<typeof useAuthContext>['signOut'];

  // Login actions
  loginWithEmail: (email: string, password: string) => Promise<AuthResult>;
  loginWithGoogle: () => Promise<AuthResult>;
  loginLoading: boolean;
  loginError: string | null;
}

export function useAuth(): UseAuthReturn {
  const context = useAuthContext();
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const loginWithEmail = async (email: string, password: string): Promise<AuthResult> => {
    setLoginLoading(true);
    setLoginError(null);

    try {
      const result = await signInWithEmail(email, password);

      if (!result.success) {
        setLoginError(result.error || 'Erro ao fazer login');
      }

      return result;
    } catch (error) {
      const errorMessage = 'Erro inesperado ao fazer login';
      setLoginError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoginLoading(false);
    }
  };

  const loginWithGoogle = async (): Promise<AuthResult> => {
    setLoginLoading(true);
    setLoginError(null);

    try {
      const result = await signInWithGoogle();

      if (!result.success) {
        setLoginError(result.error || 'Erro ao fazer login');
      }

      return result;
    } catch (error) {
      const errorMessage = 'Erro inesperado ao fazer login';
      setLoginError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoginLoading(false);
    }
  };

  return {
    // From context
    user: context.user,
    firebaseUser: context.firebaseUser,
    loading: context.loading,
    isAuthenticated: context.isAuthenticated,
    isEmailPasswordUser: context.isEmailPasswordUser,
    hasPermission: context.hasPermission,
    hasRole: context.hasRole,
    signOut: context.signOut,

    // Login actions
    loginWithEmail,
    loginWithGoogle,
    loginLoading,
    loginError,
  };
}

// Hook to check if user has access to a route
export function useRequireAuth(redirectTo: string = '/login') {
  const { isAuthenticated, loading } = useAuthContext();

  return {
    isAuthenticated,
    loading,
    shouldRedirect: !loading && !isAuthenticated,
    redirectTo,
  };
}

// Hook to check role-based access
export function useRequireRole(allowedRoles: string[], redirectTo: string = '/') {
  const { user, loading, hasRole } = useAuthContext();

  const hasAccess = user && hasRole(allowedRoles as ReturnType<typeof useAuthContext>['user'] extends { role: infer R } ? R : never);

  return {
    hasAccess,
    loading,
    shouldRedirect: !loading && !hasAccess,
    redirectTo,
  };
}
