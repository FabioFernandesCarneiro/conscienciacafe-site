'use client';

import { Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import FecharCaixaContent from '@/components/FecharCaixaContent';

function FecharCaixaPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const registerId = searchParams?.get('id') || '';

  if (!registerId) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-light">
        <p className="text-gray-mid">ID do caixa não encontrado</p>
        <button
          onClick={() => router.push('/caixa')}
          className="mt-4 text-accent"
        >
          Voltar
        </button>
      </div>
    );
  }

  return <FecharCaixaContent registerId={registerId} />;
}

export default function FecharCaixaPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-light">
          <div className="text-gray-mid">Carregando...</div>
        </div>
      }
    >
      <FecharCaixaPageContent />
    </Suspense>
  );
}
