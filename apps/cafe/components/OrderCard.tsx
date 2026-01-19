'use client';

import { useRouter } from 'next/navigation';
import { ClockIcon, UserIcon } from '@heroicons/react/24/outline';
import { formatCurrency } from '@/lib/utils/format';
import type { Order, OrderStatus } from '@/lib/types';

interface OrderCardProps {
  order: Order;
}

const STATUS_LABELS: Record<OrderStatus, string> = {
  open: 'Aberto',
  preparing: 'Preparando',
  ready: 'Pronto',
  paid: 'Pago',
  cancelled: 'Cancelado',
};

const STATUS_COLORS: Record<OrderStatus, string> = {
  open: 'bg-blue-100 text-blue-700',
  preparing: 'bg-amber-100 text-amber-700',
  ready: 'bg-green-100 text-green-700',
  paid: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-red-100 text-red-700',
};

export default function OrderCard({ order }: OrderCardProps) {
  const router = useRouter();

  const itemCount = order.items.reduce((sum, item) => sum + item.quantity, 0);
  const minutesAgo = Math.floor((Date.now() - order.createdAt.getTime()) / 60000);

  return (
    <button
      className="block w-full rounded-xl border border-gray-100 bg-white p-4 text-left shadow-sm transition hover:border-accent hover:shadow-md active:scale-[0.98]"
      onClick={() => {
        router.push(`/pedido?id=${order.id}`);
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <h3 className="font-medium text-primary">{order.customerName}</h3>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[order.status]}`}
        >
          {STATUS_LABELS[order.status]}
        </span>
      </div>

      {/* Order Summary */}
      <div className="mt-2 flex items-center gap-4 text-sm text-gray-mid">
        <span>{itemCount} {itemCount === 1 ? 'item' : 'itens'}</span>
        <span className="font-medium text-primary">
          {formatCurrency(order.total)}
        </span>
      </div>

      {/* Footer */}
      <div className="mt-3 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1 text-gray-mid">
          <ClockIcon className="h-3.5 w-3.5" />
          <span>{minutesAgo}min</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-accent/10">
            <UserIcon className="h-3 w-3 text-accent" />
          </span>
          <span className="text-gray-dark">{order.baristaName}</span>
        </div>
      </div>
    </button>
  );
}
