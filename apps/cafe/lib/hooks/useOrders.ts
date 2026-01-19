'use client';

import { useState, useEffect, useCallback } from 'react';
import type { Order, OrderItem, OrderStatus, PaymentMethod } from '@/lib/types';
import {
  createOrder,
  getOrder,
  addOrderItem,
  removeOrderItem,
  updateOrderStatus,
  addPayment,
  cancelOrder,
  subscribeToOrder,
  subscribeToActiveOrders,
} from '@/lib/firebase/orders';

/**
 * Hook for real-time active orders list
 */
export function useActiveOrders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const unsubscribe = subscribeToActiveOrders((data) => {
      setOrders(data);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  return { orders, loading, error };
}

/**
 * Hook for a single order with real-time updates
 */
export function useOrder(orderId: string | null) {
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderId) {
      setOrder(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const unsubscribe = subscribeToOrder(orderId, (data) => {
      setOrder(data);
      setLoading(false);
    });

    return unsubscribe;
  }, [orderId]);

  return { order, loading, error };
}

/**
 * Hook for order operations
 */
export function useOrderActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(
    async (data: Parameters<typeof createOrder>[0]) => {
      setLoading(true);
      setError(null);
      try {
        const order = await createOrder(data);
        return order;
      } catch (err) {
        setError('Erro ao criar pedido');
        console.error(err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const addItem = useCallback(
    async (orderId: string, item: Omit<OrderItem, 'id'>) => {
      setLoading(true);
      setError(null);
      try {
        await addOrderItem(orderId, item);
        return true;
      } catch (err) {
        setError('Erro ao adicionar item');
        console.error(err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const removeItem = useCallback(async (orderId: string, itemId: string) => {
    setLoading(true);
    setError(null);
    try {
      await removeOrderItem(orderId, itemId);
      return true;
    } catch (err) {
      setError('Erro ao remover item');
      console.error(err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateStatus = useCallback(
    async (orderId: string, status: OrderStatus) => {
      setLoading(true);
      setError(null);
      try {
        await updateOrderStatus(orderId, status);
        return true;
      } catch (err) {
        setError('Erro ao atualizar status');
        console.error(err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const pay = useCallback(
    async (orderId: string, method: PaymentMethod, amount: number): Promise<{ success: boolean; cashbackEarned?: number }> => {
      setLoading(true);
      setError(null);
      try {
        const result = await addPayment(orderId, { method, amount });
        return { success: true, cashbackEarned: result.cashbackEarned };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro ao registrar pagamento';
        setError(message);
        console.error(err);
        return { success: false };
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const cancel = useCallback(async (orderId: string) => {
    setLoading(true);
    setError(null);
    try {
      await cancelOrder(orderId);
      return true;
    } catch (err) {
      setError('Erro ao cancelar pedido');
      console.error(err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    create,
    addItem,
    removeItem,
    updateStatus,
    pay,
    cancel,
    loading,
    error,
  };
}
