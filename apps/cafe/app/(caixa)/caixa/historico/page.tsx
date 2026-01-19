'use client';

import { useRouter } from 'next/navigation';
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  ClockIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { useCashRegisterHistory } from '@/lib/hooks/useCashRegister';
import { formatCurrency } from '@/lib/utils/format';

export default function HistoricoPage() {
  const router = useRouter();
  const { registers, loading, refresh } = useCashRegisterHistory(50);

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-primary-50">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white shadow-sm">
        <div className="flex items-center gap-3 px-4 py-3">
          <button
            onClick={() => router.push('/caixa')}
            className="rounded-lg p-2 text-secondary-600 hover:bg-secondary-100"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </button>
          <div>
            <h1 className="font-semibold text-secondary-900">
              Histórico de Movimentações
            </h1>
            <p className="text-sm text-secondary-500">
              Últimos fechamentos de caixa
            </p>
          </div>
        </div>
      </header>

      <main className="p-4">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="text-secondary-500">Carregando...</div>
          </div>
        ) : registers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <ClockIcon className="mb-4 h-12 w-12 text-secondary-300" />
            <p className="text-secondary-500">
              Nenhuma movimentação encontrada
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {registers.map((register) => {
              const totalDifference = Object.values(register.payments).reduce(
                (sum, p) => sum + p.difference,
                0
              );

              return (
                <button
                  key={register.id}
                  onClick={() =>
                    router.push(`/caixa/relatorio/${register.id}`)
                  }
                  className="block w-full rounded-xl bg-white p-4 text-left shadow-sm transition hover:shadow-md"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-secondary-900">
                          {register.movementId}
                        </span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            register.status === 'closed'
                              ? 'bg-secondary-100 text-secondary-700'
                              : 'bg-green-100 text-green-700'
                          }`}
                        >
                          {register.status === 'closed' ? 'Fechado' : 'Aberto'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-secondary-500">
                        {formatDate(register.openedAt)} • {formatTime(register.openedAt)}
                        {register.closedAt && ` - ${formatTime(register.closedAt)}`}
                      </p>
                    </div>
                    <ChevronRightIcon className="h-5 w-5 text-secondary-400" />
                  </div>

                  <div className="mt-3 grid grid-cols-3 gap-3 border-t border-secondary-100 pt-3">
                    <div>
                      <p className="text-xs text-secondary-500">Vendas</p>
                      <p className="font-medium text-secondary-900">
                        {formatCurrency(register.sales.total)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-secondary-500">Pedidos</p>
                      <p className="font-medium text-secondary-900">
                        {register.stats.totalOrders}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-secondary-500">Diferença</p>
                      <p
                        className={`font-medium ${
                          totalDifference > 0
                            ? 'text-green-600'
                            : totalDifference < 0
                            ? 'text-red-600'
                            : 'text-secondary-900'
                        }`}
                      >
                        {totalDifference !== 0 && (totalDifference > 0 ? '+' : '')}
                        {formatCurrency(totalDifference)}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
