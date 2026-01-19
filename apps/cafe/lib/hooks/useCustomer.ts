'use client';

import { useState, useEffect, useCallback } from 'react';
import type { Customer } from '@/lib/types';
import {
  searchCustomers,
  getCustomer,
  createCustomer,
  updateCustomer,
  subscribeToCustomer,
  getCashbackBalance,
  redeemCashback,
} from '@/lib/firebase/customers';

/**
 * Hook for searching customers
 */
export function useCustomerSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const search = async () => {
      setLoading(true);
      setError(null);
      try {
        const customers = await searchCustomers(query);
        setResults(customers);
      } catch (err) {
        setError('Erro ao buscar clientes');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(search, 300);
    return () => clearTimeout(timeoutId);
  }, [query]);

  return {
    query,
    setQuery,
    results,
    loading,
    error,
  };
}

/**
 * Hook for getting a single customer with real-time updates
 */
export function useCustomer(customerId: string | null) {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!customerId) {
      setCustomer(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const unsubscribe = subscribeToCustomer(customerId, (data) => {
      setCustomer(data);
      setLoading(false);
    });

    return unsubscribe;
  }, [customerId]);

  return { customer, loading, error };
}

/**
 * Hook for customer operations
 */
export function useCustomerActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(
    async (data: Parameters<typeof createCustomer>[0]) => {
      setLoading(true);
      setError(null);
      try {
        const customer = await createCustomer(data);
        return customer;
      } catch (err) {
        setError('Erro ao criar cliente');
        console.error(err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const update = useCallback(
    async (customerId: string, data: Partial<Customer>) => {
      setLoading(true);
      setError(null);
      try {
        await updateCustomer(customerId, data);
        return true;
      } catch (err) {
        setError('Erro ao atualizar cliente');
        console.error(err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const useCashback = useCallback(
    async (customerId: string, amount: number, orderId: string) => {
      setLoading(true);
      setError(null);
      try {
        const result = await redeemCashback(customerId, amount, orderId);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro ao usar cashback';
        setError(message);
        console.error(err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const getBalance = useCallback(async (customerId: string) => {
    try {
      return await getCashbackBalance(customerId);
    } catch (err) {
      console.error(err);
      return 0;
    }
  }, []);

  return {
    create,
    update,
    useCashback,
    getBalance,
    loading,
    error,
  };
}
