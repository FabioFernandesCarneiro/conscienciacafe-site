import {
  ref,
  push,
  set,
  get,
  update,
  remove,
  query,
  orderByChild,
  equalTo,
  onValue,
  off,
  DataSnapshot,
} from 'firebase/database';
import { database as getDatabase } from './config';
import { getOpenCashRegister, recordPaymentToCashRegister, updateCashRegisterStats } from './cashRegister';
import { creditCashback } from './customers';
import type { Order, OrderItem, OrderStatus, Payment } from '@/lib/types';

const ORDERS_PATH = 'orders';

/**
 * Create a new order
 */
export async function createOrder(
  orderData: Omit<Order, 'id' | 'createdAt' | 'total' | 'payments'>
): Promise<Order> {
  const ordersRef = ref(getDatabase(), ORDERS_PATH);
  const newOrderRef = push(ordersRef);

  const now = new Date().toISOString();
  const total = calculateTotal(orderData.items);

  const newOrder = {
    ...orderData,
    createdAt: now,
    total,
    payments: [],
    items: orderData.items.map((item) => ({
      ...item,
      addedAt: item.addedAt instanceof Date ? item.addedAt.toISOString() : item.addedAt,
    })),
  };

  await set(newOrderRef, newOrder);

  return {
    id: newOrderRef.key!,
    ...orderData,
    createdAt: new Date(now),
    total,
    payments: [],
  };
}

/**
 * Get an order by ID
 */
export async function getOrder(orderId: string): Promise<Order | null> {
  const orderRef = ref(getDatabase(), `${ORDERS_PATH}/${orderId}`);
  const snapshot = await get(orderRef);

  if (!snapshot.exists()) {
    return null;
  }

  return parseOrder(orderId, snapshot.val());
}

/**
 * Get all active orders (not paid or cancelled)
 */
export async function getActiveOrders(): Promise<Order[]> {
  const ordersRef = ref(getDatabase(), ORDERS_PATH);
  const snapshot = await get(ordersRef);

  if (!snapshot.exists()) {
    return [];
  }

  const orders: Order[] = [];
  snapshot.forEach((child: DataSnapshot) => {
    const order = parseOrder(child.key!, child.val());
    if (order.status !== 'paid' && order.status !== 'cancelled') {
      orders.push(order);
    }
  });

  // Sort by creation time (oldest first)
  return orders.sort(
    (a, b) => a.createdAt.getTime() - b.createdAt.getTime()
  );
}

/**
 * Add item to an order
 */
export async function addOrderItem(
  orderId: string,
  item: Omit<OrderItem, 'id'>
): Promise<void> {
  const order = await getOrder(orderId);
  if (!order) throw new Error('Order not found');

  const newItem: OrderItem = {
    ...item,
    id: `item_${Date.now()}`,
    addedAt: new Date(),
  };

  const updatedItems = [...order.items, newItem];
  const total = calculateTotal(updatedItems);

  await update(ref(getDatabase(), `${ORDERS_PATH}/${orderId}`), {
    items: updatedItems.map((i) => ({
      ...i,
      addedAt: i.addedAt instanceof Date ? i.addedAt.toISOString() : i.addedAt,
    })),
    total,
  });
}

/**
 * Remove item from an order
 */
export async function removeOrderItem(
  orderId: string,
  itemId: string
): Promise<void> {
  const order = await getOrder(orderId);
  if (!order) throw new Error('Order not found');

  const updatedItems = order.items.filter((i) => i.id !== itemId);
  const total = calculateTotal(updatedItems);

  await update(ref(getDatabase(), `${ORDERS_PATH}/${orderId}`), {
    items: updatedItems.map((i) => ({
      ...i,
      addedAt: i.addedAt instanceof Date ? i.addedAt.toISOString() : i.addedAt,
    })),
    total,
  });
}

/**
 * Update order status
 */
export async function updateOrderStatus(
  orderId: string,
  status: OrderStatus
): Promise<void> {
  const updates: Record<string, unknown> = { status };

  if (status === 'paid') {
    updates.paidAt = new Date().toISOString();
  }

  await update(ref(getDatabase(), `${ORDERS_PATH}/${orderId}`), updates);
}

/**
 * Add payment to an order and record to cash register
 * Returns cashback earned if order is fully paid and customer is identified
 */
export async function addPayment(
  orderId: string,
  payment: Omit<Payment, 'paidAt'>
): Promise<{ cashbackEarned?: number }> {
  const order = await getOrder(orderId);
  if (!order) throw new Error('Order not found');

  // Check if there's an open cash register
  const openRegister = await getOpenCashRegister();
  if (!openRegister) {
    throw new Error('Não há caixa aberto. Abra um caixa antes de registrar pagamentos.');
  }

  const newPayment: Payment = {
    ...payment,
    paidAt: new Date(),
  };

  const updatedPayments = [...order.payments, newPayment];
  const totalPaid = updatedPayments.reduce((sum, p) => sum + p.amount, 0);

  const updates: Record<string, unknown> = {
    payments: updatedPayments.map((p) => ({
      ...p,
      paidAt: p.paidAt instanceof Date ? p.paidAt.toISOString() : p.paidAt,
    })),
  };

  const isFullyPaid = totalPaid >= order.total;
  let cashbackEarned: number | undefined;

  // Auto-complete order if fully paid
  if (isFullyPaid) {
    updates.status = 'paid';
    updates.paidAt = new Date().toISOString();

    // Credit cashback to customer if identified
    if (order.customerId) {
      try {
        const result = await creditCashback(order.customerId, orderId, order.total);
        cashbackEarned = result.cashbackEarned;
        updates.cashbackEarned = cashbackEarned;
      } catch (err) {
        console.error('Erro ao creditar cashback:', err);
        // Don't fail the payment if cashback fails
      }
    }
  }

  // Update the order
  await update(ref(getDatabase(), `${ORDERS_PATH}/${orderId}`), updates);

  // Record payment to cash register
  await recordPaymentToCashRegister(openRegister.id, payment.method, payment.amount);

  // If order is fully paid, update cash register statistics
  if (isFullyPaid) {
    const orderDuration = Math.floor(
      (new Date().getTime() - order.createdAt.getTime()) / 60000
    ); // in minutes
    const itemCount = order.items.reduce((sum, item) => sum + item.quantity, 0);

    await updateCashRegisterStats(openRegister.id, {
      orderTotal: order.total,
      orderDuration,
      itemCount,
    });
  }

  return { cashbackEarned };
}

/**
 * Cancel an order
 */
export async function cancelOrder(orderId: string): Promise<void> {
  await updateOrderStatus(orderId, 'cancelled');
}

/**
 * Subscribe to real-time order updates
 */
export function subscribeToOrder(
  orderId: string,
  callback: (order: Order | null) => void
): () => void {
  const orderRef = ref(getDatabase(), `${ORDERS_PATH}/${orderId}`);

  onValue(orderRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback(null);
      return;
    }
    callback(parseOrder(orderId, snapshot.val()));
  });

  return () => off(orderRef);
}

/**
 * Subscribe to all active orders (real-time)
 */
export function subscribeToActiveOrders(
  callback: (orders: Order[]) => void
): () => void {
  const ordersRef = ref(getDatabase(), ORDERS_PATH);

  onValue(ordersRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback([]);
      return;
    }

    const orders: Order[] = [];
    snapshot.forEach((child: DataSnapshot) => {
      const order = parseOrder(child.key!, child.val());
      if (order.status !== 'paid' && order.status !== 'cancelled') {
        orders.push(order);
      }
    });

    // Sort by creation time (oldest first)
    callback(orders.sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime()));
  });

  return () => off(ordersRef);
}

// Helper functions

function parseOrder(id: string, data: Record<string, unknown>): Order {
  return {
    id,
    customerId: data.customerId as string | undefined,
    customerName: data.customerName as string,
    status: data.status as OrderStatus,
    items: ((data.items as unknown[]) || []).map((item: unknown) => {
      const i = item as Record<string, unknown>;
      return {
        ...i,
        addedAt: new Date(i.addedAt as string),
      } as OrderItem;
    }),
    payments: ((data.payments as unknown[]) || []).map((payment: unknown) => {
      const p = payment as Record<string, unknown>;
      return {
        ...p,
        paidAt: new Date(p.paidAt as string),
      } as Payment;
    }),
    baristaId: data.baristaId as string,
    baristaName: data.baristaName as string,
    createdAt: new Date(data.createdAt as string),
    paidAt: data.paidAt ? new Date(data.paidAt as string) : undefined,
    total: data.total as number,
    discount: data.discount as number | undefined,
    cashbackEarned: data.cashbackEarned as number | undefined,
    cashbackUsed: data.cashbackUsed as number | undefined,
  };
}

function calculateTotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
