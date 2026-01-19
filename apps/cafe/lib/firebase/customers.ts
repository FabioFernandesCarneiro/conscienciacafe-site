import {
  ref,
  push,
  set,
  get,
  update,
  query,
  orderByChild,
  startAt,
  endAt,
  onValue,
  off,
  DataSnapshot,
} from 'firebase/database';
import { database as getDatabase } from './config';
import type { Customer, LoyaltyTier, LoyaltyTransaction } from '@/lib/types';
import { CASHBACK_RATES, TIER_THRESHOLDS } from '@/lib/types';

const CUSTOMERS_PATH = 'customers';

/**
 * Parse customer data from Firebase
 */
function parseCustomer(id: string, data: Record<string, unknown>): Customer {
  const loyalty = data.loyalty as Record<string, unknown> | undefined;
  const history = (loyalty?.history as unknown[]) || [];

  return {
    id,
    name: data.name as string,
    phone: data.phone as string,
    type: (data.type as 'b2c' | 'b2b') || 'b2c',
    companyName: data.companyName as string | undefined,
    createdAt: new Date(data.createdAt as string),
    lastVisit: new Date(data.lastVisit as string),
    totalVisits: (data.totalVisits as number) || 0,
    totalSpent: (data.totalSpent as number) || 0,
    preferences: (data.preferences as Customer['preferences']) || {},
    loyalty: {
      cashback: (loyalty?.cashback as number) || 0,
      tier: (loyalty?.tier as LoyaltyTier) || 'iniciante',
      visitsThisMonth: (loyalty?.visitsThisMonth as number) || 0,
      lastTierUpdate: loyalty?.lastTierUpdate
        ? new Date(loyalty.lastTierUpdate as string)
        : new Date(),
      history: history.map((h) => {
        const txn = h as Record<string, unknown>;
        return {
          id: txn.id as string,
          date: new Date(txn.date as string),
          type: txn.type as 'earn' | 'redeem',
          amount: txn.amount as number,
          reason: txn.reason as string,
          orderId: txn.orderId as string | undefined,
          orderTotal: txn.orderTotal as number | undefined,
        };
      }),
    },
  };
}

/**
 * Search customers by name or phone
 */
export async function searchCustomers(searchTerm: string): Promise<Customer[]> {
  const searchLower = searchTerm.toLowerCase();
  const customersRef = ref(getDatabase(), CUSTOMERS_PATH);

  // Firebase doesn't support full-text search, so we'll fetch and filter
  // For production, consider using Algolia or similar
  const snapshot = await get(customersRef);

  if (!snapshot.exists()) {
    return [];
  }

  const customers: Customer[] = [];
  snapshot.forEach((child: DataSnapshot) => {
    const data = child.val();
    const customer = parseCustomer(child.key!, data);

    // Filter by name or phone
    if (
      customer.name.toLowerCase().includes(searchLower) ||
      customer.phone.includes(searchTerm)
    ) {
      customers.push(customer);
    }
  });

  // Sort by last visit (most recent first)
  return customers.sort(
    (a, b) => b.lastVisit.getTime() - a.lastVisit.getTime()
  );
}

/**
 * Get a customer by ID
 */
export async function getCustomer(customerId: string): Promise<Customer | null> {
  const customerRef = ref(getDatabase(), `${CUSTOMERS_PATH}/${customerId}`);
  const snapshot = await get(customerRef);

  if (!snapshot.exists()) {
    return null;
  }

  return parseCustomer(customerId, snapshot.val());
}

/**
 * Create a new customer
 */
export async function createCustomer(
  customerData: Omit<Customer, 'id' | 'createdAt' | 'lastVisit' | 'totalVisits' | 'totalSpent' | 'loyalty'>
): Promise<Customer> {
  const customersRef = ref(getDatabase(), CUSTOMERS_PATH);
  const newCustomerRef = push(customersRef);

  const now = new Date().toISOString();
  const newCustomer = {
    ...customerData,
    createdAt: now,
    lastVisit: now,
    totalVisits: 0,
    totalSpent: 0,
    loyalty: {
      cashback: 0,
      tier: 'iniciante' as LoyaltyTier,
      visitsThisMonth: 0,
      lastTierUpdate: now,
      history: [],
    },
  };

  await set(newCustomerRef, newCustomer);

  return {
    id: newCustomerRef.key!,
    ...customerData,
    createdAt: new Date(now),
    lastVisit: new Date(now),
    totalVisits: 0,
    totalSpent: 0,
    loyalty: {
      cashback: 0,
      tier: 'iniciante',
      visitsThisMonth: 0,
      lastTierUpdate: new Date(now),
      history: [],
    },
  };
}

/**
 * Update customer data
 */
export async function updateCustomer(
  customerId: string,
  updates: Partial<Customer>
): Promise<void> {
  const customerRef = ref(getDatabase(), `${CUSTOMERS_PATH}/${customerId}`);

  // Convert dates to ISO strings for Firebase
  const firebaseUpdates: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(updates)) {
    if (value instanceof Date) {
      firebaseUpdates[key] = value.toISOString();
    } else {
      firebaseUpdates[key] = value;
    }
  }

  await update(customerRef, firebaseUpdates);
}

/**
 * Record a customer visit (updates lastVisit and totalVisits)
 */
export async function recordCustomerVisit(customerId: string): Promise<void> {
  const customer = await getCustomer(customerId);
  if (!customer) return;

  await updateCustomer(customerId, {
    lastVisit: new Date(),
    totalVisits: customer.totalVisits + 1,
  });
}

/**
 * Calculate the customer's tier based on visits this month
 */
export function calculateTier(visitsThisMonth: number): LoyaltyTier {
  if (visitsThisMonth >= TIER_THRESHOLDS.da_casa) return 'da_casa';
  if (visitsThisMonth >= TIER_THRESHOLDS.habitue) return 'habitue';
  if (visitsThisMonth >= TIER_THRESHOLDS.frequente) return 'frequente';
  return 'iniciante';
}

/**
 * Get the cashback rate for a customer's tier
 */
export function getCashbackRate(tier: LoyaltyTier): number {
  return CASHBACK_RATES[tier];
}

/**
 * Calculate cashback amount for an order
 */
export function calculateCashback(orderTotal: number, tier: LoyaltyTier): number {
  const rate = CASHBACK_RATES[tier];
  return Math.round(orderTotal * rate * 100) / 100; // Round to 2 decimal places
}

/**
 * Credit cashback to a customer after order payment
 */
export async function creditCashback(
  customerId: string,
  orderId: string,
  orderTotal: number
): Promise<{ cashbackEarned: number; newTier: LoyaltyTier }> {
  const customer = await getCustomer(customerId);
  if (!customer) throw new Error('Cliente não encontrado');

  const now = new Date();
  const nowISO = now.toISOString();

  // Check if we need to reset monthly visits (new month)
  const lastUpdate = customer.loyalty.lastTierUpdate;
  const isNewMonth =
    lastUpdate.getMonth() !== now.getMonth() ||
    lastUpdate.getFullYear() !== now.getFullYear();

  const visitsThisMonth = isNewMonth ? 1 : customer.loyalty.visitsThisMonth + 1;
  const newTier = calculateTier(visitsThisMonth);
  const cashbackEarned = calculateCashback(orderTotal, newTier);

  const transaction: Omit<LoyaltyTransaction, 'date'> & { date: string } = {
    id: `txn_${Date.now()}`,
    date: nowISO,
    type: 'earn',
    amount: cashbackEarned,
    reason: `Cashback ${(CASHBACK_RATES[newTier] * 100).toFixed(0)}% do pedido`,
    orderId,
    orderTotal,
  };

  const newCashback = customer.loyalty.cashback + cashbackEarned;

  await update(ref(getDatabase(), `${CUSTOMERS_PATH}/${customerId}`), {
    lastVisit: nowISO,
    totalVisits: customer.totalVisits + 1,
    totalSpent: customer.totalSpent + orderTotal,
    'loyalty/cashback': newCashback,
    'loyalty/tier': newTier,
    'loyalty/visitsThisMonth': visitsThisMonth,
    'loyalty/lastTierUpdate': nowISO,
    'loyalty/history': [
      ...customer.loyalty.history.map((h) => ({
        ...h,
        date: h.date instanceof Date ? h.date.toISOString() : h.date,
      })),
      transaction,
    ],
  });

  return { cashbackEarned, newTier };
}

/**
 * Use cashback as payment (redeem)
 */
export async function redeemCashback(
  customerId: string,
  amount: number,
  orderId: string
): Promise<{ success: boolean; remainingCashback: number }> {
  const customer = await getCustomer(customerId);
  if (!customer) throw new Error('Cliente não encontrado');

  if (customer.loyalty.cashback < amount) {
    throw new Error('Saldo de cashback insuficiente');
  }

  const now = new Date().toISOString();
  const newCashback = customer.loyalty.cashback - amount;

  const transaction: Omit<LoyaltyTransaction, 'date'> & { date: string } = {
    id: `txn_${Date.now()}`,
    date: now,
    type: 'redeem',
    amount: -amount,
    reason: 'Cashback usado no pedido',
    orderId,
  };

  await update(ref(getDatabase(), `${CUSTOMERS_PATH}/${customerId}/loyalty`), {
    cashback: newCashback,
    history: [
      ...customer.loyalty.history.map((h) => ({
        ...h,
        date: h.date instanceof Date ? h.date.toISOString() : h.date,
      })),
      transaction,
    ],
  });

  return { success: true, remainingCashback: newCashback };
}

/**
 * Get customer's current cashback balance
 */
export async function getCashbackBalance(customerId: string): Promise<number> {
  const customer = await getCustomer(customerId);
  return customer?.loyalty.cashback ?? 0;
}

/**
 * Subscribe to real-time customer updates
 */
export function subscribeToCustomer(
  customerId: string,
  callback: (customer: Customer | null) => void
): () => void {
  const customerRef = ref(getDatabase(), `${CUSTOMERS_PATH}/${customerId}`);

  const unsubscribe = onValue(customerRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback(null);
      return;
    }

    callback(parseCustomer(customerId, snapshot.val()));
  });

  return () => off(customerRef);
}
