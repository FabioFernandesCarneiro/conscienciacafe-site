'use client';

import Link from 'next/link';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import ProductImporter from '@/components/admin/ProductImporter';

export default function ImportarProdutosPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/admin/produtos"
          className="rounded-lg p-2 text-gray-mid hover:bg-gray-light hover:text-primary"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-primary">Importar Produtos</h1>
          <p className="text-gray-mid">Importe produtos de um arquivo CSV</p>
        </div>
      </div>

      {/* Importer */}
      <ProductImporter />
    </div>
  );
}
