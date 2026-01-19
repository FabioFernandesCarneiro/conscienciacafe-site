'use client';

import { useState, useCallback } from 'react';
import {
  ArrowUpTrayIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { importProducts, type ImportProgressCallback } from '@/lib/firebase/products';
import { formatCurrency } from '@/lib/utils/format';
import type { Product, Station, ProductType } from '@/lib/types';

interface ImportResult {
  imported: number;
  updated: number;
  errors: string[];
}

interface ParsedProduct extends Omit<Product, 'id'> {
  rawData?: Record<string, string>;
}

// Station mapping from CSV
const STATION_MAP: Record<string, Station> = {
  'Bebidas': 'bebidas',
  'Comidas': 'comidas',
  'Coffee Shop': 'bebidas',
  'Livraria': 'bebidas', // Default to bebidas
  'Eventos': 'bebidas',
  '': 'bebidas',
};

/**
 * Remove surrounding quotes from a string
 */
function stripQuotes(value: string): string {
  const trimmed = value.trim();
  // Remove surrounding double quotes
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return trimmed.slice(1, -1).trim();
  }
  // Remove surrounding single quotes
  if (trimmed.startsWith("'") && trimmed.endsWith("'")) {
    return trimmed.slice(1, -1).trim();
  }
  return trimmed;
}

/**
 * Parse CSV file with ; separator and UTF-8 BOM handling
 */
function parseCSV(text: string): Record<string, string>[] {
  // Remove UTF-8 BOM if present
  const cleanText = text.replace(/^\uFEFF/, '');

  const lines = cleanText.split('\n').filter((line) => line.trim());
  if (lines.length < 2) return [];

  // Get headers from first line (also strip quotes from headers)
  const headers = lines[0].split(';').map((h) => stripQuotes(h));

  // Parse remaining lines
  const rows: Record<string, string>[] = [];
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(';');
    const row: Record<string, string> = {};

    headers.forEach((header, index) => {
      // Strip quotes from values
      row[header] = stripQuotes(values[index] || '');
    });

    rows.push(row);
  }

  return rows;
}

/**
 * Convert CSV row to Product
 * Note: Firebase Realtime Database does not accept undefined values,
 * so we only include optional fields if they have actual values.
 */
function csvToProduct(row: Record<string, string>): ParsedProduct | null {
  // Required fields
  const name = row['Descrição'] || row['Descrição'] || row['Nome'];
  if (!name) return null;

  // Parse price (handles "60,00" format)
  const priceStr = row['Preço'] || row['Preco'] || '0';
  const price = parseFloat(priceStr.replace(',', '.')) || 0;

  // Get station from "Setor de impressão"
  const stationRaw = row['Setor de impressão'] || row['Setor de impressao'] || '';
  const station = STATION_MAP[stationRaw] || 'bebidas';

  // Get active status
  const visibleRaw = row['Visível'] || row['Visivel'] || 'Sim';
  const active = visibleRaw.toLowerCase() === 'sim';

  // Get optional fields (only include if they have values)
  const description = row['Detalhes']?.trim() || null;
  const code = row['Código']?.trim() || row['Codigo']?.trim() || null;
  const abbreviation = row['Abreviação']?.trim() || row['Abreviacao']?.trim() || null;
  const stockSection = row['Setor de estoque']?.trim() || null;

  // Build product object without undefined values
  const product: ParsedProduct = {
    name,
    category: row['Categoria'] || 'Outros',
    type: (row['Tipo'] || 'produto') as ProductType,
    unit: row['Unidade'] || 'UN',
    station,
    prices: {
      balcao: price,
      b2b: price,
      delivery: price,
    },
    active,
    divisible: false,
    autoWeight: false,
    isIngredient: (row['Insumo'] || '').toLowerCase() === 'sim',
    chargeCommission: false,
    printAsTicket: true,
    images: [],
    rawData: row,
  };

  // Only add optional fields if they have values (Firebase doesn't accept undefined/null)
  if (description) product.description = description;
  if (code) product.code = code;
  if (abbreviation) product.abbreviation = abbreviation;
  if (stockSection) product.stockSection = stockSection;

  return product;
}

interface ImportProgress {
  current: number;
  total: number;
  currentProduct: string;
}

export default function ProductImporter() {
  const [file, setFile] = useState<File | null>(null);
  const [parsedProducts, setParsedProducts] = useState<ParsedProduct[]>([]);
  const [importing, setImporting] = useState(false);
  const [importProgress, setImportProgress] = useState<ImportProgress | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const handleFileSelect = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setResult(null);
    setParseError(null);

    try {
      const text = await selectedFile.text();
      const rows = parseCSV(text);

      if (rows.length === 0) {
        setParseError('Arquivo CSV vazio ou formato inválido.');
        setParsedProducts([]);
        return;
      }

      const products = rows
        .map(csvToProduct)
        .filter((p): p is ParsedProduct => p !== null);

      if (products.length === 0) {
        setParseError('Nenhum produto válido encontrado. Verifique o formato do CSV.');
        setParsedProducts([]);
        return;
      }

      setParsedProducts(products);
    } catch (error) {
      console.error('Error parsing CSV:', error);
      setParseError('Erro ao ler arquivo. Verifique se é um CSV válido.');
      setParsedProducts([]);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile?.type === 'text/csv' || droppedFile?.name.endsWith('.csv')) {
        handleFileSelect(droppedFile);
      }
    },
    [handleFileSelect]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        handleFileSelect(selectedFile);
      }
    },
    [handleFileSelect]
  );

  const handleImport = async () => {
    if (parsedProducts.length === 0) return;

    setImporting(true);
    setImportProgress({ current: 0, total: parsedProducts.length, currentProduct: '' });

    try {
      // Remove rawData before importing
      const cleanProducts = parsedProducts.map(({ rawData, ...product }) => product);

      const handleProgress: ImportProgressCallback = (progress) => {
        setImportProgress(progress);
      };

      const importResult = await importProducts(cleanProducts, handleProgress);
      setResult(importResult);
    } catch (error) {
      console.error('Error importing products:', error);
      setResult({
        imported: 0,
        updated: 0,
        errors: ['Erro ao importar produtos. Tente novamente.'],
      });
    } finally {
      setImporting(false);
      setImportProgress(null);
    }
  };

  const handleReset = () => {
    setFile(null);
    setParsedProducts([]);
    setResult(null);
    setParseError(null);
    setImportProgress(null);
  };

  return (
    <div className="space-y-6">
      {/* Import Result */}
      {result && (
        <div
          className={`rounded-xl border p-6 ${
            result.errors.length > 0 ? 'border-amber-200 bg-amber-50' : 'border-green-200 bg-green-50'
          }`}
        >
          <div className="flex items-start gap-4">
            {result.errors.length > 0 ? (
              <ExclamationCircleIcon className="h-6 w-6 text-amber-600" />
            ) : (
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
            )}
            <div className="flex-1">
              <h3 className="font-medium text-primary">Importacao concluida</h3>
              <div className="mt-2 space-y-1 text-sm">
                <p className="text-green-700">{result.imported} produtos importados</p>
                {result.updated > 0 && (
                  <p className="text-blue-700">{result.updated} produtos atualizados</p>
                )}
                {result.errors.length > 0 && (
                  <div className="mt-2">
                    <p className="font-medium text-amber-700">Erros:</p>
                    <ul className="mt-1 list-inside list-disc text-amber-700">
                      {result.errors.slice(0, 5).map((error, i) => (
                        <li key={i}>{error}</li>
                      ))}
                      {result.errors.length > 5 && (
                        <li>... e mais {result.errors.length - 5} erros</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
              <button
                onClick={handleReset}
                className="mt-4 text-sm font-medium text-accent hover:text-accent-hover"
              >
                Importar outro arquivo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* File Drop Zone */}
      {!result && (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className={`relative rounded-xl border-2 border-dashed p-8 text-center transition ${
            file
              ? 'border-accent bg-accent/5'
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }`}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleInputChange}
            className="absolute inset-0 cursor-pointer opacity-0"
          />

          {file ? (
            <div className="flex flex-col items-center">
              <DocumentTextIcon className="h-12 w-12 text-accent" />
              <p className="mt-2 font-medium text-primary">{file.name}</p>
              <p className="text-sm text-gray-mid">
                {parsedProducts.length} produtos encontrados
              </p>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  handleReset();
                }}
                className="mt-2 text-sm text-gray-mid hover:text-primary"
              >
                Remover arquivo
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <ArrowUpTrayIcon className="h-12 w-12 text-gray-400" />
              <p className="mt-2 font-medium text-primary">
                Arraste o arquivo CSV aqui
              </p>
              <p className="text-sm text-gray-mid">ou clique para selecionar</p>
            </div>
          )}
        </div>
      )}

      {/* Parse Error */}
      {parseError && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-600">{parseError}</div>
      )}

      {/* Preview */}
      {parsedProducts.length > 0 && !result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-primary">
              Pré-visualização ({parsedProducts.length} produtos)
            </h3>
            <button
              onClick={handleImport}
              disabled={importing}
              className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-50"
            >
              {importing ? 'Importando...' : 'Importar Produtos'}
            </button>
          </div>

          {/* Progress Indicator */}
          {importing && importProgress && (
            <div className="rounded-lg border border-accent/20 bg-accent/5 p-4">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-gray-dark">
                  Importando: <span className="font-medium">{importProgress.currentProduct}</span>
                </span>
                <span className="font-medium text-accent">
                  {importProgress.current} / {importProgress.total}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-full rounded-full bg-accent transition-all duration-300"
                  style={{ width: `${(importProgress.current / importProgress.total) * 100}%` }}
                />
              </div>
              <p className="mt-2 text-center text-xs text-gray-mid">
                {Math.round((importProgress.current / importProgress.total) * 100)}% concluído
              </p>
            </div>
          )}

          <div className="max-h-96 overflow-auto rounded-xl border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="sticky top-0 bg-gray-light">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-dark">
                    Nome
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-dark">
                    Categoria
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-dark">
                    Estacao
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-dark">
                    Preco
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-dark">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {parsedProducts.slice(0, 50).map((product, index) => (
                  <tr key={index}>
                    <td className="px-4 py-2 text-sm text-primary">{product.name}</td>
                    <td className="px-4 py-2 text-sm text-gray-mid">{product.category}</td>
                    <td className="px-4 py-2 text-sm text-gray-mid capitalize">{product.station}</td>
                    <td className="px-4 py-2 text-right text-sm text-primary">
                      {formatCurrency(product.prices.balcao)}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <span
                        className={`inline-block h-2 w-2 rounded-full ${
                          product.active ? 'bg-green-500' : 'bg-gray-300'
                        }`}
                      />
                    </td>
                  </tr>
                ))}
                {parsedProducts.length > 50 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-2 text-center text-sm text-gray-mid">
                      ... e mais {parsedProducts.length - 50} produtos
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CSV Format Help */}
      {!file && !result && (
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h3 className="font-medium text-primary">Formato esperado do CSV</h3>
          <p className="mt-2 text-sm text-gray-mid">
            O arquivo deve usar <code className="rounded bg-gray-light px-1">;</code> como separador
            e incluir as seguintes colunas:
          </p>
          <ul className="mt-3 space-y-1 text-sm text-gray-mid">
            <li>
              <strong>Descrição</strong> - Nome do produto (obrigatorio)
            </li>
            <li>
              <strong>Preco</strong> - Preco em R$ (ex: 60,00)
            </li>
            <li>
              <strong>Categoria</strong> - Categoria do produto
            </li>
            <li>
              <strong>Código</strong> - SKU/código interno
            </li>
            <li>
              <strong>Setor de impressao</strong> - Bebidas ou Comidas
            </li>
            <li>
              <strong>Visivel</strong> - Sim ou Nao
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
