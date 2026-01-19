'use client';

import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  UserPlusIcon,
  PhoneIcon,
  StarIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { formatCurrency } from '@/lib/utils/format';

interface CustomerSearchProps {
  open: boolean;
  onClose: () => void;
}

interface CustomerResult {
  id: string;
  name: string;
  phone: string;
  type: 'b2c' | 'b2b';
  companyName?: string;
  cashback: number;
  tier: 'bronze' | 'silver' | 'gold';
  visits: number;
  lastOrder?: {
    items: string[];
    daysAgo: number;
  };
  preferences?: string[];
}

export default function CustomerSearch({ open, onClose }: CustomerSearchProps) {
  const [query, setQuery] = useState('');
  const [showNewCustomer, setShowNewCustomer] = useState(false);
  const [isB2B, setIsB2B] = useState(false);

  // Mock search results - will be replaced with Firebase
  const searchResults: CustomerResult[] = query.length >= 2
    ? ([
        {
          id: '1',
          name: 'João Silva',
          phone: '(45) 99999-1234',
          type: 'b2c' as const,
          cashback: 23.5,
          tier: 'gold' as const,
          visits: 24,
          lastOrder: {
            items: ['Flat White', 'Avocado Toast'],
            daysAgo: 3,
          },
          preferences: ['Leite de aveia', 'Cafés frutados'],
        },
        {
          id: '2',
          name: 'João Pedro',
          phone: '(45) 99888-5678',
          type: 'b2c' as const,
          cashback: 5.0,
          tier: 'bronze' as const,
          visits: 2,
        },
      ] as CustomerResult[]).filter((c) =>
        c.name.toLowerCase().includes(query.toLowerCase()) ||
        c.phone.includes(query)
      )
    : [];

  const handleSelectCustomer = (customer: CustomerResult) => {
    // Navigate to order creation with customer
    console.log('Selected customer:', customer);
    onClose();
  };

  const handleAnonymousOrder = () => {
    console.log('Starting anonymous order');
    onClose();
  };

  const tierColors = {
    bronze: 'bg-amber-100 text-amber-700',
    silver: 'bg-gray-100 text-gray-700',
    gold: 'bg-yellow-100 text-yellow-700',
  };

  const tierLabels = {
    bronze: 'Frequente',
    silver: 'Habitué',
    gold: 'Da Casa',
  };

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-start justify-center pt-4 sm:pt-12">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white shadow-xl transition-all">
                {/* Search Header */}
                <div className="flex items-center gap-3 border-b border-secondary-100 px-4 py-3">
                  <MagnifyingGlassIcon className="h-5 w-5 text-secondary-400" />
                  <input
                    type="text"
                    className="flex-1 border-0 bg-transparent text-base placeholder-secondary-400 focus:outline-none focus:ring-0"
                    placeholder="Nome ou telefone do cliente..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    autoFocus
                  />
                  <button
                    onClick={onClose}
                    className="rounded-lg p-1 text-secondary-400 hover:bg-secondary-100 hover:text-secondary-600"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                {/* Results */}
                <div className="max-h-[60vh] overflow-y-auto">
                  {/* Quick Actions */}
                  <div className="border-b border-secondary-100 px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={handleAnonymousOrder}
                        className="flex-1 rounded-lg border border-secondary-200 px-3 py-2 text-sm font-medium text-secondary-700 transition hover:bg-secondary-50"
                      >
                        Cliente Anônimo
                      </button>
                      <button
                        onClick={() => setShowNewCustomer(true)}
                        className="flex items-center gap-1 rounded-lg bg-primary-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-primary-600"
                      >
                        <UserPlusIcon className="h-4 w-4" />
                        Novo
                      </button>
                    </div>
                  </div>

                  {/* Search Results */}
                  {searchResults.length > 0 ? (
                    <div className="divide-y divide-secondary-100">
                      {searchResults.map((customer) => (
                        <button
                          key={customer.id}
                          onClick={() => handleSelectCustomer(customer)}
                          className="block w-full px-4 py-4 text-left transition hover:bg-primary-50"
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-secondary-900">
                                  {customer.name}
                                </span>
                                {customer.type === 'b2b' && (
                                  <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-xs font-medium text-indigo-700">
                                    B2B
                                  </span>
                                )}
                              </div>
                              <div className="mt-0.5 flex items-center gap-2 text-sm text-secondary-500">
                                <PhoneIcon className="h-3.5 w-3.5" />
                                {customer.phone}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="flex items-center gap-1">
                                <span
                                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${tierColors[customer.tier]}`}
                                >
                                  {tierLabels[customer.tier]}
                                </span>
                              </div>
                              {customer.cashback > 0 && (
                                <div className="mt-1 text-sm font-medium text-green-600">
                                  {formatCurrency(customer.cashback)} cashback
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Last Order */}
                          {customer.lastOrder && (
                            <div className="mt-3 rounded-lg bg-secondary-50 p-3">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-medium uppercase tracking-wide text-secondary-500">
                                  Último pedido ({customer.lastOrder.daysAgo} dias)
                                </span>
                                <button className="flex items-center gap-1 rounded bg-primary-500 px-2 py-1 text-xs font-medium text-white">
                                  <ArrowPathIcon className="h-3 w-3" />
                                  Repetir
                                </button>
                              </div>
                              <div className="mt-1 text-sm text-secondary-700">
                                {customer.lastOrder.items.join(' • ')}
                              </div>
                            </div>
                          )}

                          {/* Preferences */}
                          {customer.preferences && customer.preferences.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {customer.preferences.map((pref, i) => (
                                <span
                                  key={i}
                                  className="rounded-full bg-secondary-100 px-2 py-0.5 text-xs text-secondary-600"
                                >
                                  {pref}
                                </span>
                              ))}
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  ) : query.length >= 2 ? (
                    <div className="px-4 py-8 text-center">
                      <p className="text-secondary-500">
                        Nenhum cliente encontrado
                      </p>
                      <button
                        onClick={() => setShowNewCustomer(true)}
                        className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary-600"
                      >
                        <UserPlusIcon className="h-4 w-4" />
                        Cadastrar novo cliente
                      </button>
                    </div>
                  ) : (
                    <div className="px-4 py-8 text-center text-sm text-secondary-500">
                      Digite pelo menos 2 caracteres para buscar
                    </div>
                  )}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}
