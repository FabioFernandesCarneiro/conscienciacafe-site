'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import {
  PlusIcon,
  PencilIcon,
  CubeIcon,
  ArrowUpTrayIcon,
  FunnelIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline';
import { subscribeToProducts, deactivateProduct, reactivateProduct } from '@/lib/firebase/products';
import type { Product, Station } from '@/lib/types';
import ProductForm from '@/components/admin/ProductForm';
import { formatCurrency } from '@/lib/utils/format';

const STATION_LABELS: Record<Station, string> = {
  bebidas: 'Bebidas',
  comidas: 'Comidas',
};

const STATION_COLORS: Record<Station, string> = {
  bebidas: 'bg-blue-100 text-blue-700',
  comidas: 'bg-amber-100 text-amber-700',
};

const PAGE_SIZE = 50;

export default function ProdutosPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('active');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsubscribe = subscribeToProducts((allProducts) => {
      setProducts(allProducts);
      setLoading(false);
    }, true); // Include inactive products

    return () => unsubscribe();
  }, []);

  // Get unique categories
  const categories = Array.from(new Set(products.map((p) => p.category))).sort();

  // Filter products
  const filteredProducts = products.filter((product) => {
    // Status filter
    if (filter === 'active' && !product.active) return false;
    if (filter === 'inactive' && product.active) return false;

    // Category filter
    if (categoryFilter !== 'all' && product.category !== categoryFilter) return false;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        product.name.toLowerCase().includes(query) ||
        product.code?.toLowerCase().includes(query) ||
        product.category.toLowerCase().includes(query)
      );
    }

    return true;
  });

  // Products to display (with pagination)
  const visibleProducts = filteredProducts.slice(0, visibleCount);
  const hasMore = visibleCount < filteredProducts.length;

  // Reset visible count when filters change
  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [filter, categoryFilter, searchQuery]);

  // Infinite scroll with Intersection Observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore) {
          setVisibleCount((prev) => prev + PAGE_SIZE);
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore]);

  const handleToggleActive = async (product: Product) => {
    try {
      if (product.active) {
        await deactivateProduct(product.id);
      } else {
        await reactivateProduct(product.id);
      }
    } catch (error) {
      console.error('Error toggling product active status:', error);
    }
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setIsDuplicating(false);
    setShowForm(true);
  };

  const handleDuplicate = (product: Product) => {
    setEditingProduct(product);
    setIsDuplicating(true);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingProduct(null);
    setIsDuplicating(false);
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-gray-mid">Carregando produtos...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary">Produtos</h1>
          <p className="text-gray-mid">
            {filteredProducts.length} de {products.length} produtos
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/admin/produtos/importar"
            className="flex items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-dark transition hover:bg-gray-light"
          >
            <ArrowUpTrayIcon className="h-5 w-5" />
            Importar CSV
          </Link>
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover"
          >
            <PlusIcon className="h-5 w-5" />
            Novo Produto
          </button>
        </div>
      </div>

      {/* Search */}
      <div>
        <input
          type="text"
          placeholder="Buscar por nome, código ou categoria..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex gap-2">
          {(['active', 'inactive', 'all'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                filter === f
                  ? 'bg-primary text-white'
                  : 'bg-gray-light text-gray-dark hover:bg-gray-200'
              }`}
            >
              {f === 'active' ? 'Ativos' : f === 'inactive' ? 'Inativos' : 'Todos'}
            </button>
          ))}
        </div>

        {/* Category filter */}
        <div className="flex items-center gap-2">
          <FunnelIcon className="h-5 w-5 text-gray-mid" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="all">Todas categorias</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Product List */}
      {filteredProducts.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
          <CubeIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 font-medium text-primary">Nenhum produto encontrado</h3>
          <p className="mt-1 text-sm text-gray-mid">
            {searchQuery
              ? 'Tente uma busca diferente.'
              : filter === 'active'
              ? 'Não há produtos ativos.'
              : filter === 'inactive'
              ? 'Não há produtos inativos.'
              : 'Adicione o primeiro produto ou importe do CSV.'}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-light">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-dark">
                  Produto
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-dark sm:table-cell">
                  Categoria
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-dark md:table-cell">
                  Estacao
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-dark">
                  Preco
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-dark">
                  Acoes
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {visibleProducts.map((product) => (
                <tr
                  key={product.id}
                  className={`hover:bg-gray-50 ${!product.active ? 'opacity-50' : ''}`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-light">
                        <CubeIcon className="h-5 w-5 text-gray-mid" />
                      </div>
                      <div>
                        <div className="font-medium text-primary">{product.name}</div>
                        {product.code && (
                          <div className="text-xs text-gray-mid">Cod: {product.code}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="hidden px-4 py-3 sm:table-cell">
                    <span className="text-sm text-gray-dark">{product.category}</span>
                  </td>
                  <td className="hidden px-4 py-3 md:table-cell">
                    <span
                      className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        STATION_COLORS[product.station]
                      }`}
                    >
                      {STATION_LABELS[product.station]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-medium text-primary">
                      {formatCurrency(product.prices.balcao)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleDuplicate(product)}
                        className="rounded-lg p-2 text-gray-mid hover:bg-gray-light hover:text-primary"
                        title="Duplicar"
                      >
                        <DocumentDuplicateIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(product)}
                        className="rounded-lg p-2 text-gray-mid hover:bg-gray-light hover:text-primary"
                        title="Editar"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleToggleActive(product)}
                        className={`text-xs font-medium ${
                          product.active
                            ? 'text-red-600 hover:text-red-700'
                            : 'text-green-600 hover:text-green-700'
                        }`}
                      >
                        {product.active ? 'Desativar' : 'Ativar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Infinite scroll trigger */}
          {hasMore && (
            <div
              ref={loadMoreRef}
              className="flex items-center justify-center py-4 text-sm text-gray-mid"
            >
              Carregando mais produtos...
            </div>
          )}

          {!hasMore && filteredProducts.length > PAGE_SIZE && (
            <div className="py-3 text-center text-sm text-gray-mid">
              Mostrando todos os {filteredProducts.length} produtos
            </div>
          )}
        </div>
      )}

      {/* Product Form Modal */}
      {showForm && (
        <ProductForm
          product={editingProduct}
          isDuplicating={isDuplicating}
          onClose={handleCloseForm}
          onSuccess={handleCloseForm}
        />
      )}
    </div>
  );
}
