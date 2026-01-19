'use client';

import { useState } from 'react';
import { XMarkIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';
import { useCustomerActions } from '@/lib/hooks/useCustomer';

interface NewCustomerFormProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (customerId: string) => void;
  initialName?: string;
  initialPhone?: string;
}

export default function NewCustomerForm({
  open,
  onClose,
  onSuccess,
  initialName = '',
  initialPhone = '',
}: NewCustomerFormProps) {
  const [name, setName] = useState(initialName);
  const [phone, setPhone] = useState(initialPhone);
  const [isB2B, setIsB2B] = useState(false);
  const [companyName, setCompanyName] = useState('');

  const { create, loading, error } = useCustomerActions();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) return;

    const customer = await create({
      name: name.trim(),
      phone: phone.trim(),
      type: isB2B ? 'b2b' : 'b2c',
      companyName: isB2B ? companyName.trim() : undefined,
      preferences: {},
    });

    if (customer) {
      onSuccess(customer.id);
      onClose();
    }
  };

  const formatPhone = (value: string) => {
    // Remove non-digits
    const digits = value.replace(/\D/g, '');

    // Format as (XX) XXXXX-XXXX
    if (digits.length <= 2) {
      return digits;
    } else if (digits.length <= 7) {
      return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
    } else {
      return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-secondary-900">
            Novo Cliente
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-secondary-400 hover:bg-secondary-100 hover:text-secondary-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-secondary-700"
            >
              Nome *
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-secondary-200 px-3 py-2 text-secondary-900 placeholder-secondary-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Nome do cliente"
              required
              autoFocus
            />
          </div>

          {/* Phone */}
          <div>
            <label
              htmlFor="phone"
              className="block text-sm font-medium text-secondary-700"
            >
              Telefone
            </label>
            <input
              type="tel"
              id="phone"
              value={phone}
              onChange={(e) => setPhone(formatPhone(e.target.value))}
              className="mt-1 block w-full rounded-lg border border-secondary-200 px-3 py-2 text-secondary-900 placeholder-secondary-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="(45) 99999-9999"
            />
          </div>

          {/* B2B Toggle */}
          <div className="flex items-center justify-between rounded-lg bg-secondary-50 p-3">
            <div className="flex items-center gap-2">
              <BuildingOfficeIcon className="h-5 w-5 text-secondary-500" />
              <span className="text-sm font-medium text-secondary-700">
                Cliente B2B (empresa)
              </span>
            </div>
            <button
              type="button"
              onClick={() => setIsB2B(!isB2B)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isB2B ? 'bg-indigo-600' : 'bg-secondary-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isB2B ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Company Name (if B2B) */}
          {isB2B && (
            <div>
              <label
                htmlFor="companyName"
                className="block text-sm font-medium text-secondary-700"
              >
                Nome da Empresa
              </label>
              <input
                type="text"
                id="companyName"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-secondary-200 px-3 py-2 text-secondary-900 placeholder-secondary-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="Nome da empresa"
              />
            </div>
          )}

          {/* Error */}
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-secondary-200 px-4 py-2 text-sm font-medium text-secondary-700 transition hover:bg-secondary-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="flex-1 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Salvando...' : 'Cadastrar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
