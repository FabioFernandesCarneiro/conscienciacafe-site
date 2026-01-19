import {
  ref,
  push,
  set,
  get,
  update,
  query,
  orderByChild,
  equalTo,
  onValue,
  off,
  DataSnapshot,
} from 'firebase/database';
import { database as getDatabase } from './config';
import type {
  CashRegister,
  CashRegisterStatus,
  CashOperation,
  PaymentMethod,
  PaymentBalance,
  CashRegisterSales,
  CashRegisterStats,
} from '@/lib/types';

const CASH_REGISTERS_PATH = 'cashRegisters';

/**
 * Get the currently open cash register
 */
export async function getOpenCashRegister(): Promise<CashRegister | null> {
  const registersRef = ref(getDatabase(), CASH_REGISTERS_PATH);
  const snapshot = await get(registersRef);

  if (!snapshot.exists()) {
    return null;
  }

  let openRegister: CashRegister | null = null;

  snapshot.forEach((child: DataSnapshot) => {
    const data = child.val();
    if (data.status === 'open') {
      openRegister = parseCashRegister(child.key!, data);
    }
  });

  return openRegister;
}

/**
 * Get a cash register by ID
 */
export async function getCashRegister(registerId: string): Promise<CashRegister | null> {
  const registerRef = ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}`);
  const snapshot = await get(registerRef);

  if (!snapshot.exists()) {
    return null;
  }

  return parseCashRegister(registerId, snapshot.val());
}

/**
 * Get all cash register movements (history)
 */
export async function getCashRegisterHistory(limit = 30): Promise<CashRegister[]> {
  const registersRef = ref(getDatabase(), CASH_REGISTERS_PATH);
  const snapshot = await get(registersRef);

  if (!snapshot.exists()) {
    return [];
  }

  const registers: CashRegister[] = [];
  snapshot.forEach((child: DataSnapshot) => {
    registers.push(parseCashRegister(child.key!, child.val()));
  });

  // Sort by openedAt descending and limit
  return registers
    .sort((a, b) => b.openedAt.getTime() - a.openedAt.getTime())
    .slice(0, limit);
}

/**
 * Open a new cash register
 */
export async function openCashRegister(
  operatorId: string,
  operatorName: string,
  initialCash: number = 0
): Promise<CashRegister> {
  // Check if there's already an open register
  const existingOpen = await getOpenCashRegister();
  if (existingOpen) {
    throw new Error('Já existe um caixa aberto. Feche-o antes de abrir outro.');
  }

  // Get next movement number
  const history = await getCashRegisterHistory(1);
  const lastMovementId = history[0]?.movementId || '#0';
  const nextNumber = parseInt(lastMovementId.replace('#', '')) + 1;

  const registersRef = ref(getDatabase(), CASH_REGISTERS_PATH);
  const newRegisterRef = push(registersRef);

  const now = new Date().toISOString();
  const initialPayments: Record<PaymentMethod, PaymentBalance> = {
    cash: { expected: initialCash, counted: 0, difference: 0 },
    credit: { expected: 0, counted: 0, difference: 0 },
    debit: { expected: 0, counted: 0, difference: 0 },
    pix: { expected: 0, counted: 0, difference: 0 },
    giftcard: { expected: 0, counted: 0, difference: 0 },
    marketplace: { expected: 0, counted: 0, difference: 0 },
  };

  const initialSales: CashRegisterSales = {
    comanda: 0,
    products: 0,
    commission: 0,
    services: 0,
    discounts: 0,
    total: 0,
  };

  const initialStats: CashRegisterStats = {
    totalOrders: 0,
    canceledOrders: 0,
    canceledItems: 0,
    averageTicket: 0,
    averageTime: 0,
    averageProducts: 0,
  };

  const newRegister = {
    number: 1, // Default to Caixa 1
    movementId: `#${nextNumber}`,
    status: 'open' as CashRegisterStatus,
    openedBy: operatorId,
    openedByName: operatorName,
    openedAt: now,
    sales: initialSales,
    payments: initialPayments,
    operations: initialCash > 0
      ? [{
          id: `op_${Date.now()}`,
          type: 'insert' as const,
          amount: initialCash,
          reason: 'Fundo de caixa',
          classification: 'fundo_caixa',
          isExpense: false,
          isRevenue: false,
          createdAt: now,
          createdBy: operatorId,
          createdByName: operatorName,
        }]
      : [],
    stats: initialStats,
    notes: '',
  };

  await set(newRegisterRef, newRegister);

  return {
    id: newRegisterRef.key!,
    ...newRegister,
    openedAt: new Date(now),
    operations: newRegister.operations.map(op => ({
      ...op,
      createdAt: new Date(op.createdAt),
    })),
  };
}

/**
 * Add a cash operation (insert, withdraw, sangria)
 */
export async function addCashOperation(
  registerId: string,
  operation: Omit<CashOperation, 'id' | 'createdAt'>
): Promise<void> {
  const register = await getCashRegister(registerId);
  if (!register) throw new Error('Caixa não encontrado');
  if (register.status !== 'open') throw new Error('Caixa não está aberto');

  const now = new Date().toISOString();
  const newOperation: CashOperation = {
    ...operation,
    id: `op_${Date.now()}`,
    createdAt: new Date(now),
  };

  // Update cash expected based on operation
  const currentCash = register.payments.cash.expected;
  let newCashExpected = currentCash;

  if (operation.type === 'insert') {
    newCashExpected += operation.amount;
  } else if (operation.type === 'withdraw' || operation.type === 'sangria') {
    newCashExpected -= operation.amount;
  }

  const operations = [
    ...register.operations.map(op => ({
      ...op,
      createdAt: op.createdAt instanceof Date ? op.createdAt.toISOString() : op.createdAt,
    })),
    {
      ...newOperation,
      createdAt: now,
    },
  ];

  await update(ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}`), {
    operations,
    'payments/cash/expected': newCashExpected,
  });
}

/**
 * Record a payment from an order to the cash register
 */
export async function recordPaymentToCashRegister(
  registerId: string,
  method: PaymentMethod,
  amount: number
): Promise<void> {
  const register = await getCashRegister(registerId);
  if (!register) throw new Error('Caixa não encontrado');
  if (register.status !== 'open') throw new Error('Caixa não está aberto');

  const currentExpected = register.payments[method].expected;

  await update(ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}/payments/${method}`), {
    expected: currentExpected + amount,
  });

  // Also update sales total
  await update(ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}/sales`), {
    products: register.sales.products + amount,
    total: register.sales.total + amount,
  });
}

/**
 * Update cash register statistics when an order is completed
 */
export async function updateCashRegisterStats(
  registerId: string,
  orderData: {
    orderTotal: number;
    orderDuration: number; // in minutes
    itemCount: number;
  }
): Promise<void> {
  const register = await getCashRegister(registerId);
  if (!register) throw new Error('Caixa não encontrado');
  if (register.status !== 'open') throw new Error('Caixa não está aberto');

  const currentStats = register.stats;
  const newTotalOrders = currentStats.totalOrders + 1;

  // Calculate new averages using cumulative average formula
  // new_avg = old_avg + (new_value - old_avg) / new_count
  const newAverageTicket =
    currentStats.averageTicket +
    (orderData.orderTotal - currentStats.averageTicket) / newTotalOrders;

  const newAverageTime =
    currentStats.averageTime +
    (orderData.orderDuration - currentStats.averageTime) / newTotalOrders;

  const newAverageProducts =
    currentStats.averageProducts +
    (orderData.itemCount - currentStats.averageProducts) / newTotalOrders;

  await update(ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}/stats`), {
    totalOrders: newTotalOrders,
    averageTicket: Math.round(newAverageTicket * 100) / 100, // Round to 2 decimal places
    averageTime: Math.round(newAverageTime),
    averageProducts: Math.round(newAverageProducts * 10) / 10, // Round to 1 decimal place
  });
}

/**
 * Update counted amounts during closing
 */
export async function updateCountedAmounts(
  registerId: string,
  counts: Partial<Record<PaymentMethod, number>>
): Promise<void> {
  const register = await getCashRegister(registerId);
  if (!register) throw new Error('Caixa não encontrado');

  const updates: Record<string, unknown> = {};

  for (const [method, counted] of Object.entries(counts)) {
    const expected = register.payments[method as PaymentMethod].expected;
    updates[`payments/${method}/counted`] = counted;
    updates[`payments/${method}/difference`] = counted - expected;
  }

  await update(ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}`), updates);
}

/**
 * Close the cash register
 */
export async function closeCashRegister(
  registerId: string,
  operatorId: string,
  operatorName: string,
  notes?: string
): Promise<CashRegister> {
  const register = await getCashRegister(registerId);
  if (!register) throw new Error('Caixa não encontrado');
  if (register.status !== 'open') throw new Error('Caixa já está fechado');

  const now = new Date().toISOString();

  // Calculate final stats
  const totalProducts = register.operations.reduce((sum, op) => {
    // Count products from all orders (simplified - in real app would query orders)
    return sum;
  }, 0);

  await update(ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}`), {
    status: 'closed',
    closedBy: operatorId,
    closedByName: operatorName,
    closedAt: now,
    notes: notes || '',
  });

  return (await getCashRegister(registerId))!;
}

/**
 * Subscribe to real-time cash register updates
 */
export function subscribeToCashRegister(
  registerId: string,
  callback: (register: CashRegister | null) => void
): () => void {
  const registerRef = ref(getDatabase(), `${CASH_REGISTERS_PATH}/${registerId}`);

  onValue(registerRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback(null);
      return;
    }
    callback(parseCashRegister(registerId, snapshot.val()));
  });

  return () => off(registerRef);
}

/**
 * Subscribe to open cash register
 */
export function subscribeToOpenCashRegister(
  callback: (register: CashRegister | null) => void
): () => void {
  const registersRef = ref(getDatabase(), CASH_REGISTERS_PATH);

  onValue(registersRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback(null);
      return;
    }

    let openRegister: CashRegister | null = null;

    snapshot.forEach((child: DataSnapshot) => {
      const data = child.val();
      if (data.status === 'open') {
        openRegister = parseCashRegister(child.key!, data);
      }
    });

    callback(openRegister);
  });

  return () => off(registersRef);
}

// Helper function to parse cash register from Firebase
function parseCashRegister(id: string, data: Record<string, unknown>): CashRegister {
  return {
    id,
    number: data.number as number,
    movementId: data.movementId as string,
    status: data.status as CashRegisterStatus,
    openedBy: data.openedBy as string,
    openedAt: new Date(data.openedAt as string),
    closedBy: data.closedBy as string | undefined,
    closedAt: data.closedAt ? new Date(data.closedAt as string) : undefined,
    sales: data.sales as CashRegisterSales,
    payments: data.payments as Record<PaymentMethod, PaymentBalance>,
    operations: ((data.operations as unknown[]) || []).map((op: unknown) => {
      const o = op as Record<string, unknown>;
      return {
        ...o,
        createdAt: new Date(o.createdAt as string),
      } as CashOperation;
    }),
    stats: data.stats as CashRegisterStats,
    notes: data.notes as string | undefined,
  };
}
