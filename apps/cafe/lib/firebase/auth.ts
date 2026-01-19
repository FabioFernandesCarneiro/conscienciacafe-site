import {
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser,
  updatePassword,
  reauthenticateWithCredential,
  EmailAuthProvider,
} from 'firebase/auth';
import { auth as getAuth } from './config';
import { getUser, createUser, updateLastLogin } from './users';
import type { User, UserRole } from '@/lib/types';

const googleProvider = new GoogleAuthProvider();

export interface AuthResult {
  success: boolean;
  user?: User;
  error?: string;
  isNewUser?: boolean;
}

/**
 * Sign in with email and password
 */
export async function signInWithEmail(
  email: string,
  password: string
): Promise<AuthResult> {
  try {
    const auth = getAuth();
    const credential = await signInWithEmailAndPassword(auth, email, password);
    const firebaseUser = credential.user;

    // Get user profile from database
    const user = await getUser(firebaseUser.uid);

    if (!user) {
      // User exists in Auth but not in database - this shouldn't happen
      // but we handle it gracefully
      return {
        success: false,
        error: 'Usuário não encontrado no sistema. Contate o administrador.',
      };
    }

    if (!user.active) {
      await firebaseSignOut(auth);
      return {
        success: false,
        error: 'Usuário desativado. Contate o administrador.',
      };
    }

    // Update last login
    await updateLastLogin(firebaseUser.uid);

    return {
      success: true,
      user,
    };
  } catch (error: unknown) {
    const firebaseError = error as { code?: string; message?: string };
    console.error('[Auth] Email sign-in error:', firebaseError);

    let errorMessage = 'Erro ao fazer login';
    if (firebaseError.code === 'auth/invalid-credential') {
      errorMessage = 'Email ou senha incorretos';
    } else if (firebaseError.code === 'auth/user-not-found') {
      errorMessage = 'Usuário não encontrado';
    } else if (firebaseError.code === 'auth/wrong-password') {
      errorMessage = 'Senha incorreta';
    } else if (firebaseError.code === 'auth/too-many-requests') {
      errorMessage = 'Muitas tentativas. Tente novamente mais tarde.';
    }

    return {
      success: false,
      error: errorMessage,
    };
  }
}

/**
 * Sign in with Google
 */
export async function signInWithGoogle(): Promise<AuthResult> {
  try {
    const auth = getAuth();
    const credential = await signInWithPopup(auth, googleProvider);
    const firebaseUser = credential.user;

    // Check if user exists in database
    let user = await getUser(firebaseUser.uid);
    let isNewUser = false;

    if (!user) {
      // First time Google login - create user profile
      // New users start as inactive until a gestor activates them
      user = await createUser(firebaseUser.uid, {
        email: firebaseUser.email || '',
        name: firebaseUser.displayName || 'Novo Usuário',
        role: 'barista', // Default role
        active: false, // Needs activation
        createdAt: new Date().toISOString(),
        createdBy: 'self',
        photoURL: firebaseUser.photoURL || undefined,
      });
      isNewUser = true;

      // Sign out since they need activation
      await firebaseSignOut(auth);

      return {
        success: false,
        isNewUser: true,
        error: 'Conta criada! Aguarde a ativação pelo administrador.',
      };
    }

    if (!user.active) {
      await firebaseSignOut(auth);
      return {
        success: false,
        error: 'Usuário desativado. Contate o administrador.',
      };
    }

    // Update last login and photo
    await updateLastLogin(firebaseUser.uid);

    return {
      success: true,
      user,
      isNewUser,
    };
  } catch (error: unknown) {
    const firebaseError = error as { code?: string; message?: string };
    console.error('[Auth] Google sign-in error:', firebaseError);

    let errorMessage = 'Erro ao fazer login com Google';
    if (firebaseError.code === 'auth/popup-closed-by-user') {
      errorMessage = 'Login cancelado';
    } else if (firebaseError.code === 'auth/popup-blocked') {
      errorMessage = 'Popup bloqueado. Permita popups para este site.';
    }

    return {
      success: false,
      error: errorMessage,
    };
  }
}

/**
 * Sign out
 */
export async function signOut(): Promise<void> {
  const auth = getAuth();
  await firebaseSignOut(auth);
}

/**
 * Subscribe to auth state changes
 */
export function subscribeToAuthState(
  callback: (user: FirebaseUser | null) => void
): () => void {
  const auth = getAuth();
  return onAuthStateChanged(auth, callback);
}

/**
 * Get current Firebase user
 */
export function getCurrentFirebaseUser(): FirebaseUser | null {
  const auth = getAuth();
  return auth.currentUser;
}

export interface ChangePasswordResult {
  success: boolean;
  error?: string;
}

/**
 * Change password for email/password users
 * Requires reauthentication with current password
 */
export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<ChangePasswordResult> {
  try {
    const auth = getAuth();
    const user = auth.currentUser;

    if (!user || !user.email) {
      return {
        success: false,
        error: 'Usuário não autenticado',
      };
    }

    // Re-authenticate user with current password
    const credential = EmailAuthProvider.credential(user.email, currentPassword);
    await reauthenticateWithCredential(user, credential);

    // Update password
    await updatePassword(user, newPassword);

    return { success: true };
  } catch (error: unknown) {
    const firebaseError = error as { code?: string; message?: string };
    console.error('[Auth] Change password error:', firebaseError);

    let errorMessage = 'Erro ao trocar senha';
    if (firebaseError.code === 'auth/wrong-password') {
      errorMessage = 'Senha atual incorreta';
    } else if (firebaseError.code === 'auth/invalid-credential') {
      errorMessage = 'Senha atual incorreta';
    } else if (firebaseError.code === 'auth/weak-password') {
      errorMessage = 'Nova senha muito fraca. Use pelo menos 6 caracteres.';
    } else if (firebaseError.code === 'auth/requires-recent-login') {
      errorMessage = 'Sessao expirada. Faca login novamente.';
    }

    return {
      success: false,
      error: errorMessage,
    };
  }
}
