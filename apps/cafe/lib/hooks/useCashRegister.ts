'use client';

import { useState, useEffect, useCallback } from 'react';
import type { CashRegister, CashOperation, PaymentMethod } from '@/lib/types';
import {
  getOpenCashRegister,
  getCashRegister,
  getCashRegisterHistory,
  openCashRegister,
  addCashOperation,
  updateCountedAmounts,
  closeCashRegister,
  subscribeToCashRegister,
  subscribeToOpenCashRegister,
} from '@/lib/firebase/cashRegister';

/**
 * Hook for the currently open cash register with real-time updates
 */
export function useOpenCashRegister() {
  const [register, setRegister] = useState<CashRegister | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const unsubscribe = subscribeToOpenCashRegister((data) => {
      setRegister(data);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  return { register, loading, error };
}

/**
 * Hook for a specific cash register with real-time updates
 */
export function useCashRegister(registerId: string | null) {
  const [register, setRegister] = useState<CashRegister | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!registerId) {
      setRegister(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const unsubscribe = subscribeToCashRegister(registerId, (data) => {
      setRegister(data);
      setLoading(false);
    });

    return unsubscribe;
  }, [registerId]);

  return { register, loading, error };
}

/**
 * Hook for cash register history
 */
export function useCashRegisterHistory(limit = 30) {
  const [registers, setRegisters] = useState<CashRegister[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const history = await getCashRegisterHistory(limit);
      setRegisters(history);
    } catch (err) {
      setError('Erro ao carregar histórico');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { registers, loading, error, refresh };
}

/**
 * Hook for cash register operations
 */
export function useCashRegisterActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const open = useCallback(
    async (operatorId: string, operatorName: string, initialCash?: number) => {
      setLoading(true);
      setError(null);
      try {
        const register = await openCashRegister(operatorId, operatorName, initialCash);
        return register;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro ao abrir caixa';
        setError(message);
        console.error(err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const addOperation = useCallback(
    async (registerId: string, operation: Omit<CashOperation, 'id' | 'createdAt'>) => {
      setLoading(true);
      setError(null);
      try {
        await addCashOperation(registerId, operation);
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro ao registrar operação';
        setError(message);
        console.error(err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const updateCounts = useCallback(
    async (registerId: string, counts: Partial<Record<PaymentMethod, number>>) => {
      setLoading(true);
      setError(null);
      try {
        await updateCountedAmounts(registerId, counts);
        return true;
      } catch (err) {
        setError('Erro ao atualizar contagem');
        console.error(err);
        return false;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const close = useCallback(
    async (registerId: string, operatorId: string, operatorName: string, notes?: string) => {
      setLoading(true);
      setError(null);
      try {
        const register = await closeCashRegister(registerId, operatorId, operatorName, notes);
        return register;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro ao fechar caixa';
        setError(message);
        console.error(err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    open,
    addOperation,
    updateCounts,
    close,
    loading,
    error,
  };
}
