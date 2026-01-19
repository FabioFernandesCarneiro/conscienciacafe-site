'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeftIcon,
  ClockIcon,
  TrashIcon,
  PrinterIcon,
  CreditCardIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useOrder, useOrderActions } from '@/lib/hooks/useOrders';
import { useOpenCashRegister } from '@/lib/hooks/useCashRegister';
import { useCustomer } from '@/lib/hooks/useCustomer';
import ProductSelector from '@/components/ProductSelector';
import { formatCurrency } from '@/lib/utils/format';
import toast from 'react-hot-toast';
import type { Product, PriceChannel, LoyaltyTier } from '@/lib/types';
import { CASHBACK_RATES } from '@/lib/types';

interface Props {
  orderId: string;
}

export default function OrderContent({ orderId }: Props) {
  const router = useRouter();

  const { order, loading } = useOrder(orderId);
  const { register: openCashRegister, loading: cashRegisterLoading } = useOpenCashRegister();
  const { addItem, removeItem, pay, cancel, loading: actionLoading, error: actionError } = useOrderActions();
  const { customer } = useCustomer(order?.customerId || null);

  const [showProducts, setShowProducts] = useState(false);
  const [showPayment, setShowPayment] = useState(false);

  // Helper to format tier name
  const getTierName = (tier: LoyaltyTier): string => {
    const names: Record<LoyaltyTier, string> = {
      iniciante: 'Iniciante',
      frequente: 'Frequente',
      habitue: 'Habitue',
      da_casa: 'Da Casa',
    };
    return names[tier];
  };

  // Calculate time since order creation
  const [minutesElapsed, setMinutesElapsed] = useState(0);

  useEffect(() => {
    if (!order) return;

    const updateTime = () => {
      const now = new Date();
      const diff = Math.floor((now.getTime() - order.createdAt.getTime()) / 60000);
      setMinutesElapsed(diff);
    };

    updateTime();
    const interval = setInterval(updateTime, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [order]);

  const handleAddItem = async (product: Product, quantity: number, notes?: string) => {
    if (!order) return;

    const priceChannel: PriceChannel = 'balcao'; // TODO: Get from customer type (B2B/B2C)

    await addItem(orderId, {
      productId: product.id,
      name: product.name,
      price: product.prices[priceChannel] ?? product.prices.balcao,
      quantity,
      station: product.station,
      notes,
      addedBy: 'barista', // TODO: Get from auth
      addedAt: new Date(),
    });

    setShowProducts(false);
  };

  const handleRemoveItem = async (itemId: string) => {
    await removeItem(orderId, itemId);
  };

  const handlePrint = () => {
    // TODO: Implement printing via Web Print API
    window.print();
  };

  const handlePayment = async (method: 'cash' | 'credit' | 'debit' | 'pix') => {
    if (!order) return;

    if (!openCashRegister) {
      toast.error('Não há caixa aberto. Abra um caixa antes de registrar pagamentos.');
      setShowPayment(false);
      return;
    }

    const result = await pay(orderId, method, order.total);
    if (result.success) {
      setShowPayment(false);

      // Show success message with cashback info
      if (result.cashbackEarned && result.cashbackEarned > 0) {
        toast.success(
          `Pagamento registrado! ${order.customerName} ganhou ${formatCurrency(result.cashbackEarned)} de cashback.`,
          { duration: 5000 }
        );
      } else if (order.customerId) {
        toast.success('Pagamento registrado! Cashback creditado.');
      } else {
        toast.success('Pagamento registrado com sucesso!');
      }

      router.push('/');
    } else {
      toast.error(actionError || 'Erro ao registrar pagamento');
    }
  };

  const handleOpenPaymentModal = () => {
    if (!openCashRegister) {
      toast.error('Não há caixa aberto. Abra um caixa antes de fechar a conta.');
      return;
    }
    setShowPayment(true);
  };

  const handleCancel = async () => {
    if (confirm('Tem certeza que deseja cancelar este pedido?')) {
      await cancel(orderId);
      router.push('/');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-light">
        <div className="text-gray-mid">Carregando pedido...</div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-light">
        <p className="text-gray-mid">Pedido não encontrado</p>
        <button
          onClick={() => router.push('/')}
          className="mt-4 text-accent"
        >
          Voltar
        </button>
      </div>
    );
  }

  // Group items by station
  const bebidasItems = order.items.filter((i) => i.station === 'bebidas');
  const comidasItems = order.items.filter((i) => i.station === 'comidas');

  return (
    <div className="min-h-screen bg-gray-light">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/')}
              className="rounded-lg p-2 text-gray-mid hover:bg-gray-light"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div>
              <h1 className="font-semibold text-primary">
                {order.customerName}
              </h1>
              <div className="flex items-center gap-2 text-sm text-gray-mid">
                <ClockIcon className="h-4 w-4" />
                <span>{minutesElapsed}min</span>
                <span className="text-xs">-</span>
                <span className="capitalize">{order.status}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="rounded-lg p-2 text-gray-mid hover:bg-gray-light"
            >
              <PrinterIcon className="h-5 w-5" />
            </button>
            <button
              onClick={handleCancel}
              className="rounded-lg p-2 text-red-600 hover:bg-red-50"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Customer Cashback Info */}
        {customer && (
          <div className="border-t border-gray-100 bg-gradient-to-r from-gray-light to-white px-4 py-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-xs font-bold text-white">
                  {(CASHBACK_RATES[customer.loyalty.tier] * 100).toFixed(0)}%
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-dark">
                    {getTierName(customer.loyalty.tier)}
                  </span>
                  <span className="mx-2 text-gray-300">-</span>
                  <span className="text-sm text-gray-mid">
                    {customer.loyalty.visitsThisMonth} visitas este mes
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-mid">Cashback disponível</div>
                <div className="font-semibold text-green-600">
                  {formatCurrency(customer.loyalty.cashback)}
                </div>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Order Items */}
      <main className="p-4 pb-32">
        {/* Bebidas Section */}
        {bebidasItems.length > 0 && (
          <div className="mb-4">
            <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-blue-600">
              Bebidas
            </h2>
            <div className="space-y-2">
              {bebidasItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-lg bg-white p-3 shadow-sm"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-primary">
                        {item.quantity}x
                      </span>
                      <span className="text-gray-dark">{item.name}</span>
                    </div>
                    {item.notes && (
                      <p className="mt-1 text-sm text-gray-mid">
                        {item.notes}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-primary">
                      {formatCurrency(item.price * item.quantity)}
                    </span>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="text-gray-mid hover:text-red-500"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Comidas Section */}
        {comidasItems.length > 0 && (
          <div className="mb-4">
            <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-orange-600">
              Comidas
            </h2>
            <div className="space-y-2">
              {comidasItems.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-lg bg-white p-3 shadow-sm"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-primary">
                        {item.quantity}x
                      </span>
                      <span className="text-gray-dark">{item.name}</span>
                    </div>
                    {item.notes && (
                      <p className="mt-1 text-sm text-gray-mid">
                        {item.notes}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-primary">
                      {formatCurrency(item.price * item.quantity)}
                    </span>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="text-gray-mid hover:text-red-500"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {order.items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-gray-mid">
              Nenhum item adicionado ainda
            </p>
            <button
              onClick={() => setShowProducts(true)}
              className="mt-3 text-sm font-medium text-accent"
            >
              Adicionar produtos
            </button>
          </div>
        )}
      </main>

      {/* Bottom Actions */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white p-4 shadow-lg">
        {/* Cash Register Warning */}
        {!cashRegisterLoading && !openCashRegister && (
          <div className="mb-3 flex items-center gap-2 rounded-lg bg-amber-50 p-3 text-amber-800">
            <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0" />
            <div className="text-sm">
              <span className="font-medium">Caixa não aberto.</span>{' '}
              <button
                onClick={() => router.push('/caixa')}
                className="underline"
              >
                Abrir caixa
              </button>{' '}
              para registrar pagamentos.
            </div>
          </div>
        )}

        <div className="mb-3 flex items-center justify-between">
          <span className="text-gray-mid">Total</span>
          <span className="text-xl font-semibold text-primary">
            {formatCurrency(order.total)}
          </span>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowProducts(true)}
            className="flex-1 rounded-lg border border-accent py-3 font-medium text-accent transition hover:bg-gray-light"
          >
            Adicionar Itens
          </button>
          <button
            onClick={handleOpenPaymentModal}
            disabled={order.items.length === 0 || !openCashRegister}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-600 py-3 font-medium text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <CreditCardIcon className="h-5 w-5" />
            Fechar Conta
          </button>
        </div>
      </div>

      {/* Product Selector Modal */}
      {showProducts && (
        <div className="fixed inset-0 z-50 bg-white">
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <h2 className="font-semibold text-primary">
                Adicionar Produto
              </h2>
              <button
                onClick={() => setShowProducts(false)}
                className="text-gray-mid"
              >
                Cancelar
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <ProductSelector
                priceChannel="balcao"
                onAddItem={handleAddItem}
              />
            </div>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPayment && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/25 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-t-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-center text-lg font-semibold text-primary">
              Forma de Pagamento
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handlePayment('cash')}
                className="rounded-lg border border-gray-200 p-4 text-center transition hover:bg-gray-light"
              >
                <div className="text-2xl">R$</div>
                <div className="mt-1 font-medium text-primary">Dinheiro</div>
              </button>
              <button
                onClick={() => handlePayment('credit')}
                className="rounded-lg border border-gray-200 p-4 text-center transition hover:bg-gray-light"
              >
                <CreditCardIcon className="mx-auto h-6 w-6 text-primary" />
                <div className="mt-1 font-medium text-primary">Crédito</div>
              </button>
              <button
                onClick={() => handlePayment('debit')}
                className="rounded-lg border border-gray-200 p-4 text-center transition hover:bg-gray-light"
              >
                <CreditCardIcon className="mx-auto h-6 w-6 text-primary" />
                <div className="mt-1 font-medium text-primary">Debito</div>
              </button>
              <button
                onClick={() => handlePayment('pix')}
                className="rounded-lg border border-gray-200 p-4 text-center transition hover:bg-gray-light"
              >
                <div className="text-2xl">PIX</div>
                <div className="mt-1 font-medium text-primary">PIX</div>
              </button>
            </div>
            <button
              onClick={() => setShowPayment(false)}
              className="mt-4 w-full rounded-lg border border-gray-200 py-3 font-medium text-gray-dark"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
