#!/usr/bin/env node
/**
 * Aplica categorizações informadas pelo usuário
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const DADOS_DIR = join(import.meta.dirname, '..', 'dados');
const dbPath = join(DADOS_DIR, 'lancamentos.json');

const lancamentosDb = JSON.parse(readFileSync(dbPath, 'utf-8'));

let categorizados = 0;

for (const l of lancamentosDb.lancamentos) {
  if (l.categoria !== 'A_CATEGORIZAR') continue;

  const desc = l.descricao_original.toUpperCase();

  // Giorgio Tararthuch = Marketing
  if (desc.includes('GIORGIO TARARTHUCH')) {
    l.categoria = 'FIX_MARKETING';
    l.subcategoria = 'Giorgio Tararthuch';
    l.notas = 'Responsável pelo marketing';
    categorizados++;
    console.log('✓ Giorgio Tararthuch → FIX_MARKETING');
  }

  // Lima e Bulla = Fornecedor de Açaí
  else if (desc.includes('LIMAE BULLA') || desc.includes('LIMA E BULLA')) {
    l.categoria = 'CPV_INSUMOS';
    l.subcategoria = 'Lima e Bulla - Açaí';
    l.notas = 'Fornecedor de açaí';
    categorizados++;
    console.log('✓ Lima e Bulla → CPV_INSUMOS (Açaí)');
  }

  // Amazon = Equipamentos/Insumos para cafeteria
  else if (desc.includes('AMAZON')) {
    l.categoria = 'CPV_INSUMOS';
    l.subcategoria = 'Amazon';
    l.notas = 'Equipamentos e insumos cafeteria';
    categorizados++;
    console.log('✓ Amazon → CPV_INSUMOS');
  }

  // Mugsandmore = provavelmente canecas/equipamentos
  else if (desc.includes('MUGSANDMORE')) {
    l.categoria = 'CPV_INSUMOS';
    l.subcategoria = 'Mugsandmore';
    l.notas = 'Canecas/equipamentos';
    categorizados++;
    console.log('✓ Mugsandmore → CPV_INSUMOS');
  }

  // Mercado Importsclios = provavelmente insumos
  else if (desc.includes('IMPORTSCLIOS')) {
    l.categoria = 'CPV_INSUMOS';
    l.subcategoria = 'Imports';
    l.notas = 'Insumos importados';
    categorizados++;
    console.log('✓ Importsclios → CPV_INSUMOS');
  }

  // Pagamento de fatura do cartão = Operacional (desconsiderar no DRE)
  else if (desc === 'PAGAMENTO RECEBIDO' && l.fonte === 'cartao-credito') {
    l.categoria = 'OP_PAGAMENTO_FATURA';
    l.subcategoria = null;
    l.notas = 'Pagamento fatura cartão - não entra no DRE (despesas já estão no extrato do cartão)';
    categorizados++;
    console.log('✓ Pagamento fatura → OP_PAGAMENTO_FATURA');
  }
}

// Atualizar metadata
lancamentosDb.metadata.total_categorizados = lancamentosDb.lancamentos.filter(l => l.categoria !== 'A_CATEGORIZAR').length;
lancamentosDb.metadata.total_pendentes = lancamentosDb.lancamentos.filter(l => l.categoria === 'A_CATEGORIZAR').length;
lancamentosDb.ultima_atualizacao = new Date().toISOString().split('T')[0];

writeFileSync(dbPath, JSON.stringify(lancamentosDb, null, 2));

console.log('');
console.log('Total categorizados agora: ' + categorizados);
console.log('Pendentes restantes: ' + lancamentosDb.metadata.total_pendentes);

// Lista pendentes restantes
console.log('\n=== PENDENTES RESTANTES ===\n');
const pendentes = lancamentosDb.lancamentos.filter(l => l.categoria === 'A_CATEGORIZAR');
for (const p of pendentes) {
  console.log(`${p.id} | ${p.data} | R$ ${p.valor.toFixed(2).padStart(10)} | ${p.descricao_original.slice(0, 70)}`);
}
