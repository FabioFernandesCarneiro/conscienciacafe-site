/**
 * Formata valor para moeda brasileira (R$ 1.234,56)
 */
export function formatCurrency(value: number): string {
  return value.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}

/**
 * Formata número decimal no padrão brasileiro (1.234,56)
 */
export function formatNumber(value: number, decimals: number = 2): string {
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Converte string de preço brasileiro para número
 * Ex: "1.234,56" -> 1234.56
 */
export function parseBRCurrency(value: string): number {
  if (!value) return 0;
  // Remove R$ e espaços
  const cleaned = value.replace(/R\$\s?/g, '').trim();
  // Troca ponto por nada (separador de milhar) e vírgula por ponto (decimal)
  const normalized = cleaned.replace(/\./g, '').replace(',', '.');
  return parseFloat(normalized) || 0;
}
