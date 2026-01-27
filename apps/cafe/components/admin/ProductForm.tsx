'use client';

import { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { createProduct, updateProduct } from '@/lib/firebase/products';
import type { Product, Station, ProductType } from '@/lib/types';

interface ProductFormProps {
  product?: Product | null;
  isDuplicating?: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const STATIONS: { value: Station; label: string }[] = [
  { value: 'bebidas', label: 'Bebidas' },
  { value: 'comidas', label: 'Comidas' },
];

const DEFAULT_CATEGORIES = [
  'Adicionais',
  'Cafés Filtrados',
  'Chás',
  'Coffee Shop',
  'Doces',
  'Eventos',
  'Livros',
  'Monte seu lanche',
  'Outras Bebidas',
  'Pães de Fermentação Natural',
  'Produtos de exposição',
];

export default function ProductForm({ product, isDuplicating = false, onClose, onSuccess }: ProductFormProps) {
  const isEditing = !!product && !isDuplicating;

  // Include product's category in list if not already present
  const categories = product?.category && !DEFAULT_CATEGORIES.includes(product.category)
    ? [...DEFAULT_CATEGORIES, product.category].sort()
    : DEFAULT_CATEGORIES;

  const [formData, setFormData] = useState({
    name: product?.name || '',
    description: product?.description || '',
    category: product?.category || DEFAULT_CATEGORIES[0],
    type: product?.type || 'produto' as ProductType,
    unit: product?.unit || 'UN',
    station: product?.station || 'bebidas' as Station,
    code: product?.code || '',
    abbreviation: product?.abbreviation || '',
    priceBalcao: product?.prices.balcao || 0,
    priceB2b: product?.prices.b2b || 0,
    priceDelivery: product?.prices.delivery || 0,
    active: product?.active ?? true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Build product data without undefined values (Firebase doesn't accept them)
      const productData: Partial<Omit<Product, 'id'>> = {
        name: formData.name,
        category: formData.category,
        type: formData.type,
        unit: formData.unit,
        station: formData.station,
        prices: {
          balcao: formData.priceBalcao,
          b2b: formData.priceB2b || formData.priceBalcao,
          delivery: formData.priceDelivery || formData.priceBalcao,
        },
        active: formData.active,
        divisible: false,
        autoWeight: false,
        isIngredient: false,
        chargeCommission: false,
        printAsTicket: true,
        images: [],
      };

      // Only add optional fields if they have values
      if (formData.description) productData.description = formData.description;
      if (formData.code) productData.code = formData.code;
      if (formData.abbreviation) productData.abbreviation = formData.abbreviation;

      if (isEditing && product) {
        await updateProduct(product.id, productData);
      } else {
        await createProduct(productData as Omit<Product, 'id'>);
      }

      onSuccess();
    } catch (err) {
      console.error('Error saving product:', err);
      setError('Erro ao salvar produto. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Transition appear show={true} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg transform rounded-2xl bg-white p-6 shadow-xl transition-all">
                <div className="flex items-center justify-between">
                  <Dialog.Title className="text-xl font-bold text-primary">
                    {isDuplicating ? 'Duplicar Produto' : isEditing ? 'Editar Produto' : 'Novo Produto'}
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="rounded-lg p-2 text-gray-mid hover:bg-gray-light hover:text-primary"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                  {/* Name */}
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-dark">
                      Nome do produto *
                    </label>
                    <input
                      type="text"
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                      placeholder="Ex: Cappuccino"
                      required
                    />
                  </div>

                  {/* Category and Station */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="category" className="block text-sm font-medium text-gray-dark">
                        Categoria *
                      </label>
                      <select
                        id="category"
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                        required
                      >
                        {categories.map((cat) => (
                          <option key={cat} value={cat}>
                            {cat}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="station" className="block text-sm font-medium text-gray-dark">
                        Estacao *
                      </label>
                      <select
                        id="station"
                        value={formData.station}
                        onChange={(e) =>
                          setFormData({ ...formData, station: e.target.value as Station })
                        }
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                        required
                      >
                        {STATIONS.map((st) => (
                          <option key={st.value} value={st.value}>
                            {st.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Code and Abbreviation */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="code" className="block text-sm font-medium text-gray-dark">
                        Código
                      </label>
                      <input
                        type="text"
                        id="code"
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                        placeholder="SKU"
                      />
                    </div>

                    <div>
                      <label htmlFor="abbreviation" className="block text-sm font-medium text-gray-dark">
                        Abreviacao
                      </label>
                      <input
                        type="text"
                        id="abbreviation"
                        value={formData.abbreviation}
                        onChange={(e) => setFormData({ ...formData, abbreviation: e.target.value })}
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                        placeholder="CAPPU"
                        maxLength={10}
                      />
                    </div>
                  </div>

                  {/* Prices */}
                  <div>
                    <label className="block text-sm font-medium text-gray-dark">Precos</label>
                    <div className="mt-2 grid grid-cols-3 gap-4">
                      <div>
                        <label htmlFor="priceBalcao" className="block text-xs text-gray-mid">
                          Balcao *
                        </label>
                        <input
                          type="number"
                          id="priceBalcao"
                          value={formData.priceBalcao || ''}
                          onChange={(e) =>
                            setFormData({ ...formData, priceBalcao: parseFloat(e.target.value) || 0 })
                          }
                          className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                          placeholder="0,00"
                          step="0.01"
                          min="0"
                          required
                        />
                      </div>
                      <div>
                        <label htmlFor="priceB2b" className="block text-xs text-gray-mid">
                          B2B
                        </label>
                        <input
                          type="number"
                          id="priceB2b"
                          value={formData.priceB2b || ''}
                          onChange={(e) =>
                            setFormData({ ...formData, priceB2b: parseFloat(e.target.value) || 0 })
                          }
                          className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                          placeholder="0,00"
                          step="0.01"
                          min="0"
                        />
                      </div>
                      <div>
                        <label htmlFor="priceDelivery" className="block text-xs text-gray-mid">
                          Delivery
                        </label>
                        <input
                          type="number"
                          id="priceDelivery"
                          value={formData.priceDelivery || ''}
                          onChange={(e) =>
                            setFormData({ ...formData, priceDelivery: parseFloat(e.target.value) || 0 })
                          }
                          className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                          placeholder="0,00"
                          step="0.01"
                          min="0"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-dark">
                      Descrição
                    </label>
                    <textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={2}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                      placeholder="Descrição opcional do produto"
                    />
                  </div>

                  {/* Active Toggle (only for editing) */}
                  {isEditing && (
                    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
                      <div>
                        <span className="font-medium text-primary">Produto ativo</span>
                        <p className="text-sm text-gray-mid">
                          Produtos inativos não aparecem no cardápio
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, active: !formData.active })}
                        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 ${
                          formData.active ? 'bg-accent' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
                            formData.active ? 'translate-x-5' : 'translate-x-0'
                          }`}
                        />
                      </button>
                    </div>
                  )}

                  {/* Error */}
                  {error && (
                    <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3 pt-4">
                    <button
                      type="button"
                      onClick={onClose}
                      className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-dark transition hover:bg-gray-light"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-50"
                    >
                      {loading ? 'Salvando...' : isDuplicating ? 'Duplicar' : isEditing ? 'Salvar' : 'Adicionar'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
