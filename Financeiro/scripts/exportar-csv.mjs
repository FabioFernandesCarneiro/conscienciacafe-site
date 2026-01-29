#!/usr/bin/env node
/**
 * Exporta lançamentos para CSV para conferência
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const DADOS_DIR = join(import.meta.dirname, '..', 'dados');
const RELATORIOS_DIR = join(import.meta.dirname, '..', 'relatorios');

const dbPath = join(DADOS_DIR, 'lancamentos.json');
const lancamentosDb = JSON.parse(readFileSync(dbPath, 'utf-8'));

// Função para escapar campos CSV
function escapeCSV(value) {
  if (value === null || value === undefined) return '';
  const str = String(value);
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

// Função para formatar valor em formato brasileiro
function formatarValor(valor) {
  return valor.toFixed(2).replace('.', ',');
}

// Cabeçalho do CSV
const header = [
  'ID',
  'Data',
  'Valor',
  'Tipo',
  'Fonte',
  'Categoria',
  'Subcategoria',
  'Fornecedor/Cliente',
  'Descricao Original',
  'Notas',
  'Reconciliado'
].join(';');

// Ordenar por data
const lancamentosOrdenados = [...lancamentosDb.lancamentos].sort((a, b) => {
  const dataA = new Date(a.data);
  const dataB = new Date(b.data);
  if (dataA.getTime() !== dataB.getTime()) return dataA - dataB;
  return a.id.localeCompare(b.id);
});

// Gerar linhas
const lines = lancamentosOrdenados.map(l => {
  return [
    escapeCSV(l.id),
    l.data.split('-').reverse().join('/'), // YYYY-MM-DD -> DD/MM/YYYY
    formatarValor(l.valor),
    l.tipo === 'entrada' ? 'Entrada' : 'Saída',
    escapeCSV(l.fonte),
    escapeCSV(l.categoria),
    escapeCSV(l.subcategoria),
    escapeCSV(l.fornecedor_cliente),
    escapeCSV(l.descricao_original),
    escapeCSV(l.notas),
    l.reconciliado ? 'Sim' : 'Não'
  ].join(';');
});

// Montar CSV completo
const csv = [header, ...lines].join('\n');

// Salvar arquivo
const outputPath = join(RELATORIOS_DIR, 'lancamentos-conferencia.csv');
writeFileSync(outputPath, csv, 'utf-8');

console.log(`✓ Exportado ${lancamentosOrdenados.length} lançamentos para:`);
console.log(`  ${outputPath}`);

// Estatísticas rápidas
const totalEntradas = lancamentosOrdenados.filter(l => l.tipo === 'entrada').reduce((s, l) => s + l.valor, 0);
const totalSaidas = lancamentosOrdenados.filter(l => l.tipo === 'saida').reduce((s, l) => s + Math.abs(l.valor), 0);

console.log('');
console.log('Resumo:');
console.log(`  Total de lançamentos: ${lancamentosOrdenados.length}`);
console.log(`  Entradas: R$ ${totalEntradas.toFixed(2).replace('.', ',')}`);
console.log(`  Saídas:   R$ ${totalSaidas.toFixed(2).replace('.', ',')}`);

// Por fonte
const porFonte = {};
for (const l of lancamentosOrdenados) {
  porFonte[l.fonte] = (porFonte[l.fonte] || 0) + 1;
}
console.log('');
console.log('Por fonte:');
for (const [fonte, qtd] of Object.entries(porFonte)) {
  console.log(`  ${fonte}: ${qtd}`);
}
