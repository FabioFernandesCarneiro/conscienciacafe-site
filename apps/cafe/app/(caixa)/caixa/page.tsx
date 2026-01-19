'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  BanknotesIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  ArrowPathIcon,
  ClockIcon,
  XMarkIcon,
  CheckCircleIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useOpenCashRegister, useCashRegisterActions } from '@/lib/hooks/useCashRegister';
import { formatCurrency } from '@/lib/utils/format';
import type { PaymentMethod } from '@/lib/types';

export default function CaixaPage() {
  const router = useRouter();
  const { register, loading } = useOpenCashRegister();
  const { open, addOperation, loading: actionLoading } = useCashRegisterActions();

  const [showOpenModal, setShowOpenModal] = useState(false);
  const [showOperationModal, setShowOperationModal] = useState<'insert' | 'withdraw' | 'sangria' | null>(null);
  const [initialCash, setInitialCash] = useState('');
  const [operationAmount, setOperationAmount] = useState('');
  const [operationReason, setOperationReason] = useState('');
  const [operationClassification, setOperationClassification] = useState('');
  const [isExpense, setIsExpense] = useState(false);

  // Mock operator - in real app would come from auth
  const operator = { id: 'operator1', name: 'Fabio' };

  const handleOpenCashRegister = async () => {
    const cash = parseFloat(initialCash) || 0;
    const result = await open(operator.id, operator.name, cash);
    if (result) {
      setShowOpenModal(false);
      setInitialCash('');
    }
  };

  const handleAddOperation = async () => {
    if (!register || !showOperationModal) return;

    const amount = parseFloat(operationAmount);
    if (isNaN(amount) || amount <= 0) return;

    await addOperation(register.id, {
      type: showOperationModal,
      amount,
      reason: operationReason || getDefaultReason(showOperationModal),
      classification: operationClassification,
      destination: showOperationModal === 'sangria' ? 'Caixa da empresa' : undefined,
      isExpense: showOperationModal === 'withdraw' && isExpense,
      isRevenue: false,
      createdBy: operator.id,
    });

    setShowOperationModal(null);
    setOperationAmount('');
    setOperationReason('');
    setOperationClassification('');
    setIsExpense(false);
  };

  const getDefaultReason = (type: 'insert' | 'withdraw' | 'sangria') => {
    switch (type) {
      case 'insert': return 'Reforço de caixa';
      case 'withdraw': return 'Retirada';
      case 'sangria': return 'Sangria';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  const paymentMethods: { key: PaymentMethod; label: string }[] = [
    { key: 'cash', label: 'Dinheiro' },
    { key: 'credit', label: 'Crédito' },
    { key: 'debit', label: 'Débito' },
    { key: 'pix', label: 'PIX' },
    { key: 'giftcard', label: 'Giftcard' },
    { key: 'marketplace', label: 'Marketplace' },
  ];

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-primary-50">
        <div className="text-secondary-500">Carregando...</div>
      </div>
    );
  }

  // No open cash register - show open option
  if (!register) {
    return (
      <div className="min-h-screen bg-primary-50 p-4">
        <header className="mb-6">
          <h1 className="text-xl font-semibold text-secondary-900">Caixa</h1>
          <p className="text-sm text-secondary-500">Nenhum caixa aberto</p>
        </header>

        <div className="flex flex-col items-center justify-center py-12">
          <div className="mb-4 rounded-full bg-green-100 p-4">
            <BanknotesIcon className="h-10 w-10 text-green-600" />
          </div>
          <h2 className="mb-2 text-lg font-medium text-secondary-900">
            Abrir Caixa
          </h2>
          <p className="mb-6 text-center text-sm text-secondary-500">
            Inicie o dia abrindo o caixa com o fundo inicial
          </p>
          <button
            onClick={() => setShowOpenModal(true)}
            className="rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition hover:bg-green-700"
          >
            Abrir Caixa
          </button>
        </div>

        <div className="mt-8">
          <button
            onClick={() => router.push('/caixa/histórico')}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-secondary-200 bg-white px-4 py-3 text-sm font-medium text-secondary-700 transition hover:bg-secondary-50"
          >
            <ClockIcon className="h-5 w-5" />
            Ver Histórico de Movimentações
          </button>
        </div>

        {/* Open Cash Register Modal */}
        {showOpenModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 backdrop-blur-sm">
            <div className="mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-secondary-900">
                  Abrir Caixa
                </h2>
                <button
                  onClick={() => setShowOpenModal(false)}
                  className="text-secondary-400 hover:text-secondary-600"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-secondary-700">
                  Fundo de Caixa (R$)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={initialCash}
                  onChange={(e) => setInitialCash(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-secondary-200 px-3 py-2 text-lg text-secondary-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="0,00"
                  autoFocus
                />
                <p className="mt-1 text-xs text-secondary-500">
                  Valor em dinheiro para iniciar o caixa
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowOpenModal(false)}
                  className="flex-1 rounded-lg border border-secondary-200 px-4 py-2 font-medium text-secondary-700"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleOpenCashRegister}
                  disabled={actionLoading}
                  className="flex-1 rounded-lg bg-green-600 px-4 py-2 font-medium text-white transition hover:bg-green-700 disabled:opacity-50"
                >
                  {actionLoading ? 'Abrindo...' : 'Abrir Caixa'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Cash register is open - show dashboard
  const totalInCash = register.payments.cash.expected;
  const totalSales = register.sales.total;

  return (
    <div className="min-h-screen bg-primary-50 pb-24">
      {/* Header */}
      <header className="bg-white px-4 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold text-secondary-900">
                Caixa 1
              </h1>
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                Aberto
              </span>
            </div>
            <p className="text-sm text-secondary-500">
              {register.movementId} • Aberto às {formatTime(register.openedAt)}
            </p>
          </div>
          <button
            onClick={() => router.push(`/caixa/fechar?id=${register.id}`)}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700"
          >
            Fechar Caixa
          </button>
        </div>
      </header>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-3 p-4">
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-secondary-500">
            Vendas
          </p>
          <p className="mt-1 text-xl font-semibold text-secondary-900">
            {formatCurrency(totalSales)}
          </p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-secondary-500">
            Em Dinheiro
          </p>
          <p className="mt-1 text-xl font-semibold text-green-600">
            {formatCurrency(totalInCash)}
          </p>
        </div>
      </div>

      {/* Payment Methods Breakdown */}
      <div className="mx-4 rounded-xl bg-white p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-secondary-500">
          Por Forma de Pagamento
        </h2>
        <div className="space-y-2">
          {paymentMethods.map(({ key, label }) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm text-secondary-600">{label}</span>
              <span className="font-medium text-secondary-900">
                {formatCurrency(register.payments[key].expected)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Operations History */}
      {register.operations.length > 0 && (
        <div className="mx-4 mt-4 rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-secondary-500">
            Operações do Dia
          </h2>
          <div className="space-y-2">
            {register.operations.map((op) => (
              <div
                key={op.id}
                className="flex items-center justify-between rounded-lg bg-secondary-50 p-3"
              >
                <div>
                  <span className="text-sm font-medium text-secondary-900">
                    {op.reason}
                  </span>
                  <span className="ml-2 text-xs text-secondary-500">
                    {formatTime(op.createdAt)}
                  </span>
                </div>
                <span
                  className={`font-medium ${
                    op.type === 'insert'
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {op.type === 'insert' ? '+' : '-'}
                  {formatCurrency(op.amount)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottom Actions */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-secondary-200 bg-white p-4">
        <div className="grid grid-cols-3 gap-3">
          <button
            onClick={() => setShowOperationModal('insert')}
            className="flex flex-col items-center gap-1 rounded-lg border border-green-200 bg-green-50 p-3 transition hover:bg-green-100"
          >
            <ArrowDownTrayIcon className="h-6 w-6 text-green-600" />
            <span className="text-xs font-medium text-green-700">Inserir</span>
          </button>
          <button
            onClick={() => setShowOperationModal('withdraw')}
            className="flex flex-col items-center gap-1 rounded-lg border border-red-200 bg-red-50 p-3 transition hover:bg-red-100"
          >
            <ArrowUpTrayIcon className="h-6 w-6 text-red-600" />
            <span className="text-xs font-medium text-red-700">Retirar</span>
          </button>
          <button
            onClick={() => setShowOperationModal('sangria')}
            className="flex flex-col items-center gap-1 rounded-lg border border-amber-200 bg-amber-50 p-3 transition hover:bg-amber-100"
          >
            <ArrowPathIcon className="h-6 w-6 text-amber-600" />
            <span className="text-xs font-medium text-amber-700">Sangria</span>
          </button>
        </div>
      </div>

      {/* Operation Modal */}
      {showOperationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-secondary-900">
                {showOperationModal === 'insert' && 'Inserir Dinheiro'}
                {showOperationModal === 'withdraw' && 'Retirar Dinheiro'}
                {showOperationModal === 'sangria' && 'Realizar Sangria'}
              </h2>
              <button
                onClick={() => setShowOperationModal(null)}
                className="text-secondary-400 hover:text-secondary-600"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700">
                  Valor (R$) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={operationAmount}
                  onChange={(e) => setOperationAmount(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-secondary-200 px-3 py-2 text-lg text-secondary-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="0,00"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700">
                  Motivo
                </label>
                <input
                  type="text"
                  value={operationReason}
                  onChange={(e) => setOperationReason(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-secondary-200 px-3 py-2 text-secondary-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder={getDefaultReason(showOperationModal)}
                />
              </div>

              {showOperationModal === 'withdraw' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-secondary-700">
                      Classificação
                    </label>
                    <select
                      value={operationClassification}
                      onChange={(e) => setOperationClassification(e.target.value)}
                      className="mt-1 block w-full rounded-lg border border-secondary-200 px-3 py-2 text-secondary-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    >
                      <option value="">Selecionar...</option>
                      <option value="despesa_operacional">Despesa Operacional</option>
                      <option value="pagamento_fornecedor">Pagamento Fornecedor</option>
                      <option value="pagamento_funcionário">Pagamento Funcionário</option>
                      <option value="outro">Outro</option>
                    </select>
                  </div>

                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={isExpense}
                      onChange={(e) => setIsExpense(e.target.checked)}
                      className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-secondary-700">
                      Registrar como despesa
                    </span>
                  </label>
                </>
              )}

              {showOperationModal === 'sangria' && (
                <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
                  O valor será transferido para o Caixa da Empresa
                </div>
              )}
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setShowOperationModal(null)}
                className="flex-1 rounded-lg border border-secondary-200 px-4 py-2 font-medium text-secondary-700"
              >
                Cancelar
              </button>
              <button
                onClick={handleAddOperation}
                disabled={actionLoading || !operationAmount}
                className={`flex-1 rounded-lg px-4 py-2 font-medium text-white transition disabled:opacity-50 ${
                  showOperationModal === 'insert'
                    ? 'bg-green-600 hover:bg-green-700'
                    : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {actionLoading ? 'Salvando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
