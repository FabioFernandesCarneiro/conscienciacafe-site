import { ref, get, set, update, push, onValue, off, query, orderByChild, equalTo, DataSnapshot } from 'firebase/database';
import { database as getDatabase } from './config';
import type { Product, PriceChannel } from '@/lib/types';

const PRODUCTS_PATH = 'products';

/**
 * Get all active products
 */
export async function getProducts(): Promise<Product[]> {
  const productsRef = ref(getDatabase(), PRODUCTS_PATH);
  const snapshot = await get(productsRef);

  if (!snapshot.exists()) {
    return [];
  }

  const products: Product[] = [];
  snapshot.forEach((child: DataSnapshot) => {
    const data = child.val();
    if (data.active) {
      products.push({
        id: child.key!,
        ...data,
      });
    }
  });

  // Sort alphabetically by name
  return products.sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));
}

/**
 * Get products by category
 */
export async function getProductsByCategory(category: string): Promise<Product[]> {
  const products = await getProducts();
  return products.filter((p) => p.category === category);
}

/**
 * Get all unique categories
 */
export async function getCategories(): Promise<string[]> {
  const products = await getProducts();
  const categories = new Set(products.map((p) => p.category));
  return Array.from(categories).sort();
}

/**
 * Get a product by ID
 */
export async function getProduct(productId: string): Promise<Product | null> {
  const productRef = ref(getDatabase(), `${PRODUCTS_PATH}/${productId}`);
  const snapshot = await get(productRef);

  if (!snapshot.exists()) {
    return null;
  }

  return {
    id: productId,
    ...snapshot.val(),
  };
}

/**
 * Get product price for a specific channel
 */
export function getProductPrice(product: Product, channel: PriceChannel): number {
  return product.prices[channel] ?? product.prices.balcao;
}

/**
 * Subscribe to real-time product updates
 * @param callback Function to call with products
 * @param includeInactive If true, includes inactive products (for admin)
 */
export function subscribeToProducts(
  callback: (products: Product[]) => void,
  includeInactive = false
): () => void {
  const productsRef = ref(getDatabase(), PRODUCTS_PATH);

  onValue(productsRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback([]);
      return;
    }

    const products: Product[] = [];
    snapshot.forEach((child: DataSnapshot) => {
      const data = child.val();
      if (includeInactive || data.active) {
        products.push({
          id: child.key!,
          ...data,
        });
      }
    });

    // Sort alphabetically by name
    callback(
      products.sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))
    );
  });

  return () => off(productsRef);
}

/**
 * Create a new product
 */
export async function createProduct(
  data: Omit<Product, 'id'>
): Promise<Product> {
  const productsRef = ref(getDatabase(), PRODUCTS_PATH);
  const newRef = push(productsRef);

  await set(newRef, data);

  return {
    id: newRef.key!,
    ...data,
  };
}

/**
 * Update a product
 */
export async function updateProduct(
  productId: string,
  data: Partial<Omit<Product, 'id'>>
): Promise<void> {
  const productRef = ref(getDatabase(), `${PRODUCTS_PATH}/${productId}`);
  await update(productRef, data);
}

/**
 * Deactivate a product (soft delete)
 */
export async function deactivateProduct(productId: string): Promise<void> {
  await updateProduct(productId, { active: false });
}

/**
 * Reactivate a product
 */
export async function reactivateProduct(productId: string): Promise<void> {
  await updateProduct(productId, { active: true });
}

/**
 * Progress callback for import operations
 */
export type ImportProgressCallback = (progress: {
  current: number;
  total: number;
  currentProduct: string;
}) => void;

/**
 * Import products from CSV data
 * Creates new products or updates existing ones (by code)
 */
export async function importProducts(
  products: Omit<Product, 'id'>[],
  onProgress?: ImportProgressCallback
): Promise<{ imported: number; updated: number; errors: string[] }> {
  const errors: string[] = [];
  let imported = 0;
  let updated = 0;
  const total = products.length;

  for (let i = 0; i < products.length; i++) {
    const product = products[i];

    // Report progress
    if (onProgress) {
      onProgress({
        current: i + 1,
        total,
        currentProduct: product.name,
      });
    }

    try {
      // Check if product with same code already exists
      if (product.code) {
        const existing = await getProductByCode(product.code);
        if (existing) {
          // Update existing product
          await updateProduct(existing.id, product);
          updated++;
          continue;
        }
      }

      await createProduct(product);
      imported++;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      errors.push(`Erro ao importar "${product.name}": ${errorMsg}`);
    }
  }

  return { imported, updated, errors };
}

/**
 * Get product by code (uses indexed query for performance)
 */
export async function getProductByCode(code: string): Promise<Product | null> {
  const productsRef = ref(getDatabase(), PRODUCTS_PATH);
  const codeQuery = query(productsRef, orderByChild('code'), equalTo(code));
  const snapshot = await get(codeQuery);

  if (!snapshot.exists()) {
    return null;
  }

  // Query returns an object with matching products, get the first one
  let product: Product | null = null;
  snapshot.forEach((child: DataSnapshot) => {
    product = {
      id: child.key!,
      ...child.val(),
    };
    return true; // Stop after first match
  });

  return product;
}

/**
 * Get all products including inactive (for admin)
 */
export async function getAllProducts(): Promise<Product[]> {
  const productsRef = ref(getDatabase(), PRODUCTS_PATH);
  const snapshot = await get(productsRef);

  if (!snapshot.exists()) {
    return [];
  }

  const products: Product[] = [];
  snapshot.forEach((child: DataSnapshot) => {
    products.push({
      id: child.key!,
      ...child.val(),
    });
  });

  // Sort alphabetically by name
  return products.sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));
}
