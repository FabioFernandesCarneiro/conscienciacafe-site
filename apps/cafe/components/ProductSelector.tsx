'use client';

import { useState, useMemo } from 'react';
import { MagnifyingGlassIcon, PlusIcon, MinusIcon } from '@heroicons/react/24/outline';
import { useProducts, useProductPrice } from '@/lib/hooks/useProducts';
import { formatCurrency } from '@/lib/utils/format';
import type { Product, PriceChannel, Station } from '@/lib/types';

interface ProductSelectorProps {
  priceChannel?: PriceChannel;
  onAddItem: (product: Product, quantity: number, notes?: string) => void;
}

interface CartItem {
  product: Product;
  quantity: number;
  notes?: string;
}

export default function ProductSelector({
  priceChannel = 'balcao',
  onAddItem,
}: ProductSelectorProps) {
  const { products, categories, productsByCategory, loading } = useProducts();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [notes, setNotes] = useState('');

  // Filter products by search query
  const filteredProducts = useMemo(() => {
    if (!searchQuery.trim()) {
      return selectedCategory
        ? productsByCategory[selectedCategory] || []
        : products;
    }

    const query = searchQuery.toLowerCase();
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        p.code?.toLowerCase().includes(query) ||
        p.abbreviation?.toLowerCase().includes(query)
    );
  }, [products, selectedCategory, productsByCategory, searchQuery]);

  const handleSelectProduct = (product: Product) => {
    setSelectedProduct(product);
    setQuantity(1);
    setNotes('');
  };

  const handleAddToOrder = () => {
    if (!selectedProduct) return;

    onAddItem(selectedProduct, quantity, notes.trim() || undefined);
    setSelectedProduct(null);
    setQuantity(1);
    setNotes('');
  };

  const getPrice = (product: Product) => {
    return product.prices[priceChannel] ?? product.prices.balcao;
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-secondary-500">Carregando produtos...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Search Bar */}
      <div className="border-b border-secondary-100 px-4 py-3">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-secondary-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-secondary-200 bg-secondary-50 py-2 pl-10 pr-4 text-sm placeholder-secondary-400 focus:border-primary-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="Buscar produto..."
          />
        </div>
      </div>

      {/* Categories */}
      {!searchQuery && (
        <div className="scrollbar-hide flex gap-2 overflow-x-auto border-b border-secondary-100 px-4 py-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition ${
              selectedCategory === null
                ? 'bg-primary-500 text-white'
                : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
            }`}
          >
            Todos
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition ${
                selectedCategory === category
                  ? 'bg-primary-500 text-white'
                  : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      )}

      {/* Product Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {filteredProducts.map((product) => (
            <button
              key={product.id}
              onClick={() => handleSelectProduct(product)}
              className={`flex flex-col rounded-xl border p-3 text-left transition ${
                selectedProduct?.id === product.id
                  ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-500'
                  : 'border-secondary-200 bg-white hover:border-primary-300 hover:shadow-sm'
              }`}
            >
              {/* Product Image Placeholder */}
              <div className="mb-2 aspect-square rounded-lg bg-secondary-100">
                {product.images?.[0] && (
                  <img
                    src={product.images[0]}
                    alt={product.name}
                    className="h-full w-full rounded-lg object-cover"
                  />
                )}
              </div>

              {/* Product Info */}
              <div className="flex-1">
                <h3 className="text-sm font-medium text-secondary-900 line-clamp-2">
                  {product.name}
                </h3>
                <div className="mt-1 flex items-center justify-between">
                  <span className="text-sm font-semibold text-primary-600">
                    {formatCurrency(getPrice(product))}
                  </span>
                  <span
                    className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                      product.station === 'bebidas'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-orange-100 text-orange-700'
                    }`}
                  >
                    {product.station === 'bebidas' ? 'Bebidas' : 'Comidas'}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>

        {filteredProducts.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-secondary-500">Nenhum produto encontrado</p>
          </div>
        )}
      </div>

      {/* Product Detail / Add to Order */}
      {selectedProduct && (
        <div className="border-t border-secondary-200 bg-white p-4 shadow-lg">
          <div className="mb-3 flex items-start justify-between">
            <div>
              <h3 className="font-medium text-secondary-900">
                {selectedProduct.name}
              </h3>
              <p className="text-sm text-secondary-500">
                {formatCurrency(getPrice(selectedProduct))} cada
              </p>
            </div>
            <button
              onClick={() => setSelectedProduct(null)}
              className="text-secondary-400 hover:text-secondary-600"
            >
              ✕
            </button>
          </div>

          {/* Quantity Selector */}
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-medium text-secondary-700">
              Quantidade
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary-100 text-secondary-600 hover:bg-secondary-200"
              >
                <MinusIcon className="h-4 w-4" />
              </button>
              <span className="w-8 text-center font-medium">{quantity}</span>
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary-100 text-secondary-600 hover:bg-secondary-200"
              >
                <PlusIcon className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Notes */}
          <div className="mb-4">
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-lg border border-secondary-200 px-3 py-2 text-sm placeholder-secondary-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Observações (ex: sem açúcar, extra quente...)"
              maxLength={255}
            />
          </div>

          {/* Add Button */}
          <button
            onClick={handleAddToOrder}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-500 py-3 font-medium text-white transition hover:bg-primary-600 active:scale-[0.98]"
          >
            <PlusIcon className="h-5 w-5" />
            Adicionar {formatCurrency(getPrice(selectedProduct) * quantity)}
          </button>
        </div>
      )}
    </div>
  );
}
