'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useRouter } from 'next/navigation';
import OrderContent from '@/components/OrderContent';

function OrderPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderId = searchParams?.get('id') || '';

  if (!orderId) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-light">
        <p className="text-gray-mid">ID do pedido não encontrado</p>
        <button
          onClick={() => router.push('/')}
          className="mt-4 text-accent"
        >
          Voltar
        </button>
      </div>
    );
  }

  return <OrderContent orderId={orderId} />;
}

export default function OrderPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-light">
          <div className="text-gray-mid">Carregando pedido...</div>
        </div>
      }
    >
      <OrderPageContent />
    </Suspense>
  );
}
