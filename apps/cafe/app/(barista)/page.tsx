'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import { MagnifyingGlassIcon, PlusIcon } from '@heroicons/react/24/outline';
import CustomerSearch from '@/components/CustomerSearch';
import OrderCard from '@/components/OrderCard';
import UserMenu from '@/components/UserMenu';
import { subscribeToActiveOrders } from '@/lib/firebase/orders';
import type { Order } from '@/lib/types';

export default function BaristaHome() {
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeOrders, setActiveOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = subscribeToActiveOrders((orders) => {
      setActiveOrders(orders);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="min-h-screen bg-gray-light pb-20">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white shadow-sm lg:hidden">
        <div className="px-4 py-3 flex items-center justify-between">
          <Image
            src="/images/logo.png"
            alt="Consciência Café"
            width={120}
            height={40}
            className="h-8 w-auto"
            unoptimized
          />
          <UserMenu showName />
        </div>

        {/* Search Bar */}
        <div className="px-4 pb-3">
          <button
            onClick={() => setSearchOpen(true)}
            className="flex w-full items-center gap-3 rounded-xl border border-gray-200 bg-gray-light px-4 py-3 text-left text-gray-mid transition hover:border-accent hover:bg-white"
          >
            <MagnifyingGlassIcon className="h-5 w-5" />
            <span>Buscar cliente por nome ou telefone...</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="px-4 py-4">
        {/* Active Orders Section */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wide text-gray-dark">
            Pedidos Ativos ({activeOrders.length})
          </h2>
          <button
            onClick={() => setSearchOpen(true)}
            className="flex items-center gap-1 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-accent-hover active:scale-95"
          >
            <PlusIcon className="h-4 w-4" />
            Novo
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-mid">Carregando pedidos...</div>
          </div>
        )}

        {/* Orders Grid */}
        {!loading && activeOrders.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {activeOrders.map((order) => (
              <OrderCard key={order.id} order={order} />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && activeOrders.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-4 rounded-full bg-gray-200 p-4">
              <MagnifyingGlassIcon className="h-8 w-8 text-gray-mid" />
            </div>
            <h3 className="text-lg font-medium text-primary">
              Nenhum pedido ativo
            </h3>
            <p className="mt-1 text-sm text-gray-mid">
              Busque um cliente para iniciar um novo pedido
            </p>
            <button
              onClick={() => setSearchOpen(true)}
              className="mt-4 flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover"
            >
              <PlusIcon className="h-5 w-5" />
              Novo Pedido
            </button>
          </div>
        )}
      </main>

      {/* Customer Search Modal */}
      <CustomerSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
