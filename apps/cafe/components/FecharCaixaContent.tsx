'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PrinterIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { useCashRegister, useCashRegisterActions } from '@/lib/hooks/useCashRegister';
import type { PaymentMethod } from '@/lib/types';

interface CountedAmounts {
  cash: string;
  credit: string;
  debit: string;
  pix: string;
  giftcard: string;
  marketplace: string;
}

interface CashCount {
  c100: string;
  c50: string;
  c20: string;
  c10: string;
  c5: string;
  c2: string;
  c1: string;
  m50: string;
  m25: string;
  m10: string;
  m05: string;
}

const PAYMENT_METHODS: { key: PaymentMethod; label: string }[] = [
  { key: 'cash', label: 'Dinheiro' },
  { key: 'credit', label: 'Crédito' },
  { key: 'debit', label: 'Débito' },
  { key: 'pix', label: 'PIX' },
  { key: 'giftcard', label: 'Giftcard' },
  { key: 'marketplace', label: 'Marketplace' },
];

const CASH_DENOMINATIONS = [
  { key: 'c100', label: 'R$ 100', value: 100 },
  { key: 'c50', label: 'R$ 50', value: 50 },
  { key: 'c20', label: 'R$ 20', value: 20 },
  { key: 'c10', label: 'R$ 10', value: 10 },
  { key: 'c5', label: 'R$ 5', value: 5 },
  { key: 'c2', label: 'R$ 2', value: 2 },
  { key: 'c1', label: 'R$ 1', value: 1 },
  { key: 'm50', label: 'R$ 0,50', value: 0.5 },
  { key: 'm25', label: 'R$ 0,25', value: 0.25 },
  { key: 'm10', label: 'R$ 0,10', value: 0.1 },
  { key: 'm05', label: 'R$ 0,05', value: 0.05 },
];

interface Props {
  registerId: string;
}

export default function FecharCaixaContent({ registerId }: Props) {
  const router = useRouter();
  const { register, loading } = useCashRegister(registerId);
  const { updateCounts, close, loading: actionLoading } = useCashRegisterActions();

  const [step, setStep] = useState<'count' | 'confirm' | 'done'>('count');
  const [showCashBreakdown, setShowCashBreakdown] = useState(false);
  const [notes, setNotes] = useState('');
  const [countedAmounts, setCountedAmounts] = useState<CountedAmounts>({
    cash: '',
    credit: '',
    debit: '',
    pix: '',
    giftcard: '',
    marketplace: '',
  });
  const [cashCount, setCashCount] = useState<CashCount>({
    c100: '',
    c50: '',
    c20: '',
    c10: '',
    c5: '',
    c2: '',
    c1: '',
    m50: '',
    m25: '',
    m10: '',
    m05: '',
  });

  // Mock operator - in real app would come from auth
  const operator = { id: 'operator1', name: 'Fabio' };

  // Calculate total from cash breakdown
  const cashFromBreakdown = useMemo(() => {
    return CASH_DENOMINATIONS.reduce((sum, denom) => {
      const count = parseInt(cashCount[denom.key as keyof CashCount]) || 0;
      return sum + count * denom.value;
    }, 0);
  }, [cashCount]);

  // Update cash counted amount when breakdown changes
  const handleCashCountChange = (key: keyof CashCount, value: string) => {
    setCashCount((prev) => ({ ...prev, [key]: value }));
    // Auto-update cash counted amount
    const newTotal = CASH_DENOMINATIONS.reduce((sum, denom) => {
      const count = denom.key === key
        ? parseInt(value) || 0
        : parseInt(cashCount[denom.key as keyof CashCount]) || 0;
      return sum + count * denom.value;
    }, 0);
    setCountedAmounts((prev) => ({ ...prev, cash: newTotal.toFixed(2) }));
  };

  // Calculate differences
  const differences = useMemo((): Record<PaymentMethod, number> => {
    const result: Record<PaymentMethod, number> = {
      cash: 0,
      credit: 0,
      debit: 0,
      pix: 0,
      giftcard: 0,
      marketplace: 0,
    };

    if (!register) return result;

    PAYMENT_METHODS.forEach(({ key }) => {
      const expected = register.payments[key].expected;
      const counted = parseFloat(countedAmounts[key]) || 0;
      result[key] = counted - expected;
    });
    return result;
  }, [register, countedAmounts]);

  const totalDifference = useMemo(() => {
    return (Object.values(differences) as number[]).reduce((sum, diff) => sum + diff, 0);
  }, [differences]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const handleProceedToConfirm = async () => {
    if (!register) return;

    // Save counted amounts
    const counts: Partial<Record<PaymentMethod, number>> = {};
    PAYMENT_METHODS.forEach(({ key }) => {
      counts[key] = parseFloat(countedAmounts[key]) || 0;
    });

    await updateCounts(register.id, counts);
    setStep('confirm');
  };

  const handleClose = async () => {
    if (!register) return;

    const result = await close(register.id, operator.id, operator.name, notes);
    if (result) {
      setStep('done');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-light">
        <div className="text-gray-mid">Carregando...</div>
      </div>
    );
  }

  if (!register) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-light">
        <p className="text-gray-mid">Caixa não encontrado</p>
        <button
          onClick={() => router.push('/caixa')}
          className="mt-4 text-accent"
        >
          Voltar
        </button>
      </div>
    );
  }

  if (step === 'done') {
    return (
      <div className="min-h-screen bg-gray-light p-4">
        <div className="flex flex-col items-center justify-center py-12">
          <div className="mb-4 rounded-full bg-green-100 p-4">
            <CheckCircleIcon className="h-12 w-12 text-green-600" />
          </div>
          <h1 className="mb-2 text-xl font-semibold text-primary">
            Caixa Fechado
          </h1>
          <p className="mb-6 text-gray-mid">
            {register.movementId} - Fechado com sucesso
          </p>

          <div className="flex gap-3">
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 rounded-lg border border-gray-dark bg-white px-4 py-2 font-medium text-gray-dark"
            >
              <PrinterIcon className="h-5 w-5" />
              Imprimir Cupom
            </button>
            <button
              onClick={() => router.push('/caixa')}
              className="rounded-lg bg-accent px-4 py-2 font-medium text-white hover:bg-accent-hover"
            >
              Voltar ao Caixa
            </button>
          </div>
        </div>

        {/* Print-only Report */}
        <div className="hidden print:block">
          <CashRegisterReport register={register} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-light pb-24">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white shadow-sm">
        <div className="flex items-center gap-3 px-4 py-3">
          <button
            onClick={() => step === 'count' ? router.push('/caixa') : setStep('count')}
            className="rounded-lg p-2 text-gray-mid hover:bg-gray-light"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </button>
          <div>
            <h1 className="font-semibold text-primary">
              Fechar Caixa
            </h1>
            <p className="text-sm text-gray-mid">
              {register.movementId} - {step === 'count' ? 'Conferência' : 'Confirmação'}
            </p>
          </div>
        </div>

        {/* Step Indicator */}
        <div className="flex border-t border-gray-light">
          <div
            className={`flex-1 py-2 text-center text-sm font-medium ${
              step === 'count'
                ? 'border-b-2 border-accent text-accent'
                : 'text-gray-mid'
            }`}
          >
            1. Conferência
          </div>
          <div
            className={`flex-1 py-2 text-center text-sm font-medium ${
              step === 'confirm'
                ? 'border-b-2 border-accent text-accent'
                : 'text-gray-mid'
            }`}
          >
            2. Confirmação
          </div>
        </div>
      </header>

      {step === 'count' && (
        <main className="p-4">
          {/* Payment Methods Verification */}
          <div className="rounded-xl bg-white p-4 shadow-sm">
            <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-gray-mid">
              Conferir Valores
            </h2>

            <div className="space-y-4">
              {PAYMENT_METHODS.map(({ key, label }) => (
                <div key={key}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-dark">
                      {label}
                    </span>
                    <span className="text-sm text-gray-mid">
                      Sistema: {formatCurrency(register.payments[key].expected)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-mid">R$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={countedAmounts[key]}
                      onChange={(e) =>
                        setCountedAmounts((prev) => ({
                          ...prev,
                          [key]: e.target.value,
                        }))
                      }
                      className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-right text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                      placeholder="0,00"
                    />
                  </div>

                  {/* Cash Breakdown (only for cash) */}
                  {key === 'cash' && (
                    <div className="mt-2">
                      <button
                        onClick={() => setShowCashBreakdown(!showCashBreakdown)}
                        className="flex items-center gap-1 text-sm text-accent"
                      >
                        {showCashBreakdown ? (
                          <ChevronUpIcon className="h-4 w-4" />
                        ) : (
                          <ChevronDownIcon className="h-4 w-4" />
                        )}
                        Contar cédulas e moedas
                      </button>

                      {showCashBreakdown && (
                        <div className="mt-3 grid grid-cols-2 gap-2 rounded-lg bg-gray-light p-3">
                          {CASH_DENOMINATIONS.map((denom) => (
                            <div key={denom.key} className="flex items-center gap-2">
                              <span className="w-16 text-xs text-gray-mid">
                                {denom.label}
                              </span>
                              <input
                                type="number"
                                min="0"
                                value={cashCount[denom.key as keyof CashCount]}
                                onChange={(e) =>
                                  handleCashCountChange(
                                    denom.key as keyof CashCount,
                                    e.target.value
                                  )
                                }
                                className="w-16 rounded border border-gray-300 px-2 py-1 text-center text-sm"
                                placeholder="0"
                              />
                            </div>
                          ))}
                          <div className="col-span-2 mt-2 border-t border-gray-300 pt-2">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-gray-dark">Total:</span>
                              <span className="font-semibold text-primary">
                                {formatCurrency(cashFromBreakdown)}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div className="mt-4 rounded-xl bg-white p-4 shadow-sm">
            <label className="block text-sm font-medium text-gray-dark">
              Observações
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Observações sobre o fechamento..."
              rows={3}
            />
          </div>
        </main>
      )}

      {step === 'confirm' && (
        <main className="p-4">
          {/* Summary */}
          <div className="rounded-xl bg-white p-4 shadow-sm">
            <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-gray-mid">
              Resumo do Fechamento
            </h2>

            {/* Sales */}
            <div className="mb-4 border-b border-gray-200 pb-4">
              <h3 className="mb-2 font-medium text-primary">Vendas</h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-mid">Produtos</span>
                  <span>{formatCurrency(register.sales.products)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-mid">Descontos</span>
                  <span className="text-red-600">
                    -{formatCurrency(register.sales.discounts)}
                  </span>
                </div>
                <div className="flex justify-between font-medium">
                  <span>Total</span>
                  <span>{formatCurrency(register.sales.total)}</span>
                </div>
              </div>
            </div>

            {/* Verification Table */}
            <div className="mb-4">
              <h3 className="mb-2 font-medium text-primary">
                Conferência de Caixa
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left">
                      <th className="pb-2 font-medium text-gray-mid">Forma</th>
                      <th className="pb-2 text-right font-medium text-gray-mid">Sistema</th>
                      <th className="pb-2 text-right font-medium text-gray-mid">Conferido</th>
                      <th className="pb-2 text-right font-medium text-gray-mid">Diferença</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PAYMENT_METHODS.map(({ key, label }) => {
                      const diff = differences[key] || 0;
                      return (
                        <tr key={key} className="border-b border-gray-100">
                          <td className="py-2">{label}</td>
                          <td className="py-2 text-right">
                            {formatCurrency(register.payments[key].expected)}
                          </td>
                          <td className="py-2 text-right">
                            {formatCurrency(parseFloat(countedAmounts[key]) || 0)}
                          </td>
                          <td
                            className={`py-2 text-right font-medium ${
                              diff > 0
                                ? 'text-green-600'
                                : diff < 0
                                ? 'text-red-600'
                                : 'text-gray-mid'
                            }`}
                          >
                            {diff > 0 && '+'}
                            {formatCurrency(diff)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="font-medium">
                      <td className="pt-2">Total</td>
                      <td className="pt-2 text-right">
                        {formatCurrency(
                          PAYMENT_METHODS.reduce(
                            (sum, { key }) => sum + register.payments[key].expected,
                            0
                          )
                        )}
                      </td>
                      <td className="pt-2 text-right">
                        {formatCurrency(
                          PAYMENT_METHODS.reduce(
                            (sum, { key }) =>
                              sum + (parseFloat(countedAmounts[key]) || 0),
                            0
                          )
                        )}
                      </td>
                      <td
                        className={`pt-2 text-right ${
                          totalDifference > 0
                            ? 'text-green-600'
                            : totalDifference < 0
                            ? 'text-red-600'
                            : 'text-gray-mid'
                        }`}
                      >
                        {totalDifference > 0 && '+'}
                        {formatCurrency(totalDifference)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Difference Warning */}
            {totalDifference !== 0 && (
              <div
                className={`flex items-start gap-2 rounded-lg p-3 ${
                  totalDifference > 0 ? 'bg-green-50' : 'bg-red-50'
                }`}
              >
                <ExclamationTriangleIcon
                  className={`h-5 w-5 flex-shrink-0 ${
                    totalDifference > 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                />
                <div>
                  <p
                    className={`font-medium ${
                      totalDifference > 0 ? 'text-green-800' : 'text-red-800'
                    }`}
                  >
                    {totalDifference > 0 ? 'Sobra no caixa' : 'Falta no caixa'}
                  </p>
                  <p
                    className={`text-sm ${
                      totalDifference > 0 ? 'text-green-700' : 'text-red-700'
                    }`}
                  >
                    Diferença de {formatCurrency(Math.abs(totalDifference))}
                  </p>
                </div>
              </div>
            )}

            {/* Statistics */}
            <div className="mt-4 border-t border-gray-200 pt-4">
              <h3 className="mb-2 font-medium text-primary">Estatísticas</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-mid">Total de pedidos</span>
                  <p className="font-medium">{register.stats.totalOrders}</p>
                </div>
                <div>
                  <span className="text-gray-mid">Ticket médio</span>
                  <p className="font-medium">
                    {formatCurrency(register.stats.averageTicket || 0)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-mid">Cancelamentos</span>
                  <p className="font-medium">{register.stats.canceledOrders}</p>
                </div>
                <div>
                  <span className="text-gray-mid">Tempo médio</span>
                  <p className="font-medium">{register.stats.averageTime || 0} min</p>
                </div>
              </div>
            </div>

            {/* Notes */}
            {notes && (
              <div className="mt-4 border-t border-gray-200 pt-4">
                <h3 className="mb-1 font-medium text-primary">Observações</h3>
                <p className="text-sm text-gray-mid">{notes}</p>
              </div>
            )}
          </div>
        </main>
      )}

      {/* Bottom Actions */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white p-4">
        {step === 'count' && (
          <button
            onClick={handleProceedToConfirm}
            className="w-full rounded-lg bg-accent py-3 font-medium text-white transition hover:bg-accent-hover"
          >
            Revisar Fechamento
          </button>
        )}

        {step === 'confirm' && (
          <div className="flex gap-3">
            <button
              onClick={() => setStep('count')}
              className="flex-1 rounded-lg border border-gray-300 py-3 font-medium text-gray-dark"
            >
              Voltar
            </button>
            <button
              onClick={handleClose}
              disabled={actionLoading}
              className="flex-1 rounded-lg bg-red-600 py-3 font-medium text-white transition hover:bg-red-700 disabled:opacity-50"
            >
              {actionLoading ? 'Fechando...' : 'Confirmar Fechamento'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Print-only Report Component
function CashRegisterReport({ register }: { register: NonNullable<ReturnType<typeof useCashRegister>['register']> }) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const formatDateTime = (date: Date) => {
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div style={{ fontFamily: 'Courier New, monospace', fontSize: '12px', width: '80mm', padding: '8px' }}>
      <div style={{ textAlign: 'center', borderBottom: '1px dashed #000', paddingBottom: '8px', marginBottom: '8px' }}>
        <div style={{ fontSize: '14px', fontWeight: 'bold' }}>CONSCIENCIA CAFE</div>
        <div>RELATORIO DE FECHAMENTO</div>
      </div>

      <div style={{ marginBottom: '8px' }}>
        <strong>Caixa:</strong> Caixa {register.number}<br />
        <strong>Movimentacao:</strong> {register.movementId}<br />
        <strong>Status:</strong> {register.status === 'closed' ? 'FECHADO' : 'ABERTO'}<br />
        <br />
        <strong>Abertura:</strong> {formatDateTime(register.openedAt)}<br />
        {register.closedAt && (
          <>
            <strong>Fechamento:</strong> {formatDateTime(register.closedAt)}<br />
          </>
        )}
      </div>

      <div style={{ borderTop: '1px dashed #000', borderBottom: '1px dashed #000', padding: '8px 0', marginBottom: '8px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>VENDAS</div>
        <table style={{ width: '100%' }}>
          <tbody>
            <tr>
              <td>Produtos</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(register.sales.products)}</td>
            </tr>
            <tr>
              <td>Descontos</td>
              <td style={{ textAlign: 'right' }}>-{formatCurrency(register.sales.discounts)}</td>
            </tr>
            <tr style={{ fontWeight: 'bold' }}>
              <td>TOTAL</td>
              <td style={{ textAlign: 'right' }}>{formatCurrency(register.sales.total)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style={{ marginBottom: '8px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>CONFERENCIA</div>
        <table style={{ width: '100%' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #000' }}>
              <th style={{ textAlign: 'left' }}>Forma</th>
              <th style={{ textAlign: 'right' }}>Sistema</th>
              <th style={{ textAlign: 'right' }}>Conferido</th>
              <th style={{ textAlign: 'right' }}>Dif</th>
            </tr>
          </thead>
          <tbody>
            {PAYMENT_METHODS.map(({ key, label }) => (
              <tr key={key}>
                <td>{label}</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(register.payments[key].expected)}</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(register.payments[key].counted)}</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(register.payments[key].difference)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {register.operations.length > 0 && (
        <div style={{ marginBottom: '8px' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>OPERACOES</div>
          {register.operations.map((op) => (
            <div key={op.id} style={{ marginBottom: '4px' }}>
              {op.type === 'insert' ? '+' : '-'}
              {formatCurrency(op.amount)} - {op.reason}
            </div>
          ))}
        </div>
      )}

      <div style={{ borderTop: '1px dashed #000', paddingTop: '8px', marginTop: '8px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>ESTATISTICAS</div>
        <div>Pedidos: {register.stats.totalOrders}</div>
        <div>Ticket Medio: {formatCurrency(register.stats.averageTicket || 0)}</div>
        <div>Cancelamentos: {register.stats.canceledOrders}</div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '16px', borderTop: '1px dashed #000', paddingTop: '8px' }}>
        Consciência Café
      </div>
    </div>
  );
}
