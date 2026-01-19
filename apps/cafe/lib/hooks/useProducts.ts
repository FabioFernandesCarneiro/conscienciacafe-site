'use client';

import { useState, useEffect, useMemo } from 'react';
import type { Product, PriceChannel } from '@/lib/types';
import {
  getProducts,
  getCategories,
  getProductPrice,
  subscribeToProducts,
} from '@/lib/firebase/products';

/**
 * Hook for products with real-time updates
 */
export function useProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const unsubscribe = subscribeToProducts((data) => {
      setProducts(data);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Extract unique categories
  const categories = useMemo(() => {
    const cats = new Set(products.map((p) => p.category));
    return Array.from(cats).sort();
  }, [products]);

  // Group products by category
  const productsByCategory = useMemo(() => {
    const grouped: Record<string, Product[]> = {};
    for (const product of products) {
      if (!grouped[product.category]) {
        grouped[product.category] = [];
      }
      grouped[product.category].push(product);
    }
    return grouped;
  }, [products]);

  return {
    products,
    categories,
    productsByCategory,
    loading,
    error,
  };
}

/**
 * Hook for products filtered by category
 */
export function useProductsByCategory(category: string | null) {
  const { products, loading, error } = useProducts();

  const filtered = useMemo(() => {
    if (!category) return products;
    return products.filter((p) => p.category === category);
  }, [products, category]);

  return {
    products: filtered,
    loading,
    error,
  };
}

/**
 * Hook for getting product price based on channel (B2C vs B2B)
 */
export function useProductPrice(
  product: Product | null,
  channel: PriceChannel = 'balcao'
) {
  return useMemo(() => {
    if (!product) return 0;
    return getProductPrice(product, channel);
  }, [product, channel]);
}
