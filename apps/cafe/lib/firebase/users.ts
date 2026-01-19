import { ref, get, set, update, onValue, off, query, orderByChild, equalTo } from 'firebase/database';
import { database as getDatabase } from './config';
import type { User, UserRole } from '@/lib/types';

const USERS_PATH = 'users';

/**
 * Get a user by ID
 */
export async function getUser(userId: string): Promise<User | null> {
  const userRef = ref(getDatabase(), `${USERS_PATH}/${userId}`);
  const snapshot = await get(userRef);

  if (!snapshot.exists()) {
    return null;
  }

  return {
    id: userId,
    ...snapshot.val(),
  };
}

/**
 * Get all users
 */
export async function getUsers(): Promise<User[]> {
  const usersRef = ref(getDatabase(), USERS_PATH);
  const snapshot = await get(usersRef);

  if (!snapshot.exists()) {
    return [];
  }

  const users: User[] = [];
  snapshot.forEach((child) => {
    users.push({
      id: child.key!,
      ...child.val(),
    });
  });

  return users.sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * Get active users
 */
export async function getActiveUsers(): Promise<User[]> {
  const users = await getUsers();
  return users.filter((u) => u.active);
}

/**
 * Get users by role
 */
export async function getUsersByRole(role: UserRole): Promise<User[]> {
  const users = await getUsers();
  return users.filter((u) => u.role === role && u.active);
}

/**
 * Create a new user
 */
export async function createUser(
  userId: string,
  data: Omit<User, 'id'>
): Promise<User> {
  const userRef = ref(getDatabase(), `${USERS_PATH}/${userId}`);

  await set(userRef, data);

  return {
    id: userId,
    ...data,
  };
}

/**
 * Update a user
 */
export async function updateUser(
  userId: string,
  data: Partial<Omit<User, 'id'>>
): Promise<void> {
  const userRef = ref(getDatabase(), `${USERS_PATH}/${userId}`);
  await update(userRef, data);
}

/**
 * Update user's last login
 */
export async function updateLastLogin(userId: string): Promise<void> {
  await updateUser(userId, {
    lastLogin: new Date().toISOString(),
  });
}

/**
 * Deactivate a user (soft delete)
 */
export async function deactivateUser(userId: string): Promise<void> {
  await updateUser(userId, { active: false });
}

/**
 * Reactivate a user
 */
export async function reactivateUser(userId: string): Promise<void> {
  await updateUser(userId, { active: true });
}

/**
 * Check if user exists by email
 */
export async function getUserByEmail(email: string): Promise<User | null> {
  const users = await getUsers();
  return users.find((u) => u.email.toLowerCase() === email.toLowerCase()) || null;
}

/**
 * Subscribe to user changes
 */
export function subscribeToUser(
  userId: string,
  callback: (user: User | null) => void
): () => void {
  const userRef = ref(getDatabase(), `${USERS_PATH}/${userId}`);

  onValue(userRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback(null);
      return;
    }

    callback({
      id: userId,
      ...snapshot.val(),
    });
  });

  return () => off(userRef);
}

/**
 * Subscribe to all users
 */
export function subscribeToUsers(
  callback: (users: User[]) => void
): () => void {
  const usersRef = ref(getDatabase(), USERS_PATH);

  onValue(usersRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback([]);
      return;
    }

    const users: User[] = [];
    snapshot.forEach((child) => {
      users.push({
        id: child.key!,
        ...child.val(),
      });
    });

    callback(users.sort((a, b) => a.name.localeCompare(b.name)));
  });

  return () => off(usersRef);
}
