#!/usr/bin/env node
/**
 * Script para categorização de itens pendentes
 *
 * Aplica regras adicionais para categorizar automaticamente
 * lançamentos que ficaram como A_CATEGORIZAR.
 *
 * Uso: node categorizar-pendentes.mjs
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const FINANCEIRO_DIR = join(import.meta.dirname, '..');
const DADOS_DIR = join(FINANCEIRO_DIR, 'dados');

let lancamentosDb = JSON.parse(readFileSync(join(DADOS_DIR, 'lancamentos.json'), 'utf-8'));
let pendentesDb = JSON.parse(readFileSync(join(DADOS_DIR, 'pendentes.json'), 'utf-8'));

// Regras adicionais para categorização
const regrasAdicionais = {
  // Aluguel
  'B R T ASSESSORIA IMOBILIARIA': { categoria: 'FIX_ALUGUEL', subcategoria: 'BRT' },

  // Contador
  'PROGRESSO CONTABILIDADE': { categoria: 'FIX_CONTADOR', subcategoria: 'Progresso' },

  // Sistemas
  'OMIEXPERIENCE': { categoria: 'FIX_SISTEMA', subcategoria: 'Omie' },
  'IG*NOTAVAREJO': { categoria: 'FIX_SISTEMA', subcategoria: 'NotaVarejo' },

  // Internet/Telefone
  'STI TELECOM': { categoria: 'FIX_ADMIN', subcategoria: 'Internet' },

  // Agua
  'SANEPAR': { categoria: 'FIX_AGUA', subcategoria: 'Sanepar' },
  'COMPANHIA DE SANEAMENTO': { categoria: 'FIX_AGUA', subcategoria: 'Sanepar' },

  // Energia
  'COPEL': { categoria: 'FIX_ENERGIA', subcategoria: 'Copel' },
  'DÉBITO EM CONTA': { categoria: 'FIX_ENERGIA', subcategoria: 'Copel - Debito Automatico' },

  // Impostos
  'DAS-SIMPLES NACIONAL': { categoria: 'IMP_DAS', subcategoria: null },
  'RECEITA FED-DARF': { categoria: 'IMP_DARF', subcategoria: null },
  'PREF MUN FOZ DO IGUA': { categoria: 'IMP_PREFEITURA', subcategoria: 'ISS' },
  'PM FOZ DO IGUACU': { categoria: 'IMP_PREFEITURA', subcategoria: 'ISS' },
  'MINISTERIO DA FAZENDA': { categoria: 'IMP_DARF', subcategoria: 'DARF' },

  // Fornecedores CPV
  'OLIVA FOODS': { categoria: 'CPV_INSUMOS', subcategoria: 'Oliva Foods' },
  'ROTTA DISTRIBUIDORA': { categoria: 'CPV_INSUMOS', subcategoria: 'Rotta' },
  'INDUSTRIA E COMERCIO DE LATICI': { categoria: 'CPV_INSUMOS', subcategoria: 'Laticinios' },
  'NESTLE BRASIL': { categoria: 'CPV_INSUMOS', subcategoria: 'Nestle' },
  'POLINA COMERCIAL DE ALIMENTOS': { categoria: 'CPV_INSUMOS', subcategoria: 'Polina' },
  'J G INDUSTRIA E COMERCIO DE ALIMENTOS': { categoria: 'CPV_INSUMOS', subcategoria: 'JG Alimentos' },
  'FRIMESA': { categoria: 'CPV_INSUMOS', subcategoria: 'Frimesa' },
  'GRUPO PEREIRA': { categoria: 'CPV_INSUMOS', subcategoria: 'Grupo Pereira' },
  'PEREIRA E FRIGOTTO': { categoria: 'CPV_INSUMOS', subcategoria: 'Pereira e Frigotto' },
  'CARLOS EDUARDO FERREIRA PAES ARTESA': { categoria: 'CPV_OUTROS', subcategoria: 'Artesa' },
  'ROTA COLONIAL': { categoria: 'CPV_INSUMOS', subcategoria: 'Rota Colonial' },

  // Frete
  'MID TRANSPORTES': { categoria: 'VAR_FRETE', subcategoria: 'Mid' },
  'PAULINERIS TRANSPORTES': { categoria: 'VAR_FRETE', subcategoria: 'Paulineris' },

  // Medicina do trabalho
  'GENUSCLIN': { categoria: 'FIX_ADMIN', subcategoria: 'Medicina do Trabalho' },

  // Marketing/Design
  'GRAFIMAR': { categoria: 'FIX_MARKETING', subcategoria: 'Grafimar' },
  'ENCOPRINT': { categoria: 'FIX_MARKETING', subcategoria: 'Encoprint' },
  'EDITORA PRIMAZIA': { categoria: 'FIX_MARKETING', subcategoria: 'Primazia' },

  // Mercado Livre / Shopee
  'SHPP BRASIL': { categoria: 'VAR_EMBALAGENS', subcategoria: 'Shopee' },
  'MERCADOLIVRE': { categoria: 'VAR_EMBALAGENS', subcategoria: 'Mercado Livre' },
  'MERCADOPAGO': { categoria: 'VAR_EMBALAGENS', subcategoria: 'Mercado Pago' },

  // Transporte
  'FOZ DO IGUACU PASSAGEN': { categoria: 'FIX_ADMIN', subcategoria: 'Transporte' },

  // B2B (Pagamento Recebido)
  'PAGAMENTO RECEBIDO - FLOR DE TRIGO': { categoria: 'REC_B2B', subcategoria: 'Flor de Trigo' },
  'PAGAMENTO RECEBIDO - DOM KARAMELLO': { categoria: 'REC_B2B', subcategoria: 'Dom Karamello' },
  'PAGAMENTO RECEBIDO - MY CAT': { categoria: 'REC_B2B', subcategoria: 'My Cat Cafe' },
  'PAGAMENTO RECEBIDO - PETIT CUISINE': { categoria: 'REC_B2B', subcategoria: 'Petit Cuisine' },
  'PAGAMENTO RECEBIDO - BUBBLE MIX': { categoria: 'REC_B2B', subcategoria: 'Bubble Mix' },
  'PAGAMENTO RECEBIDO - CAFETERIA E ARQUITETURA': { categoria: 'REC_B2B', subcategoria: 'Cafeteria e Arquitetura' },

  // Operacional
  'PAGAMENTO DE FATURA': { categoria: 'OP_PAGAMENTO_FATURA', subcategoria: null },
  'APLICAÇÃO RDB': { categoria: 'OP_TRANSFERENCIA', subcategoria: 'Investimento' },

  // Investimentos
  'ESMAG FOZ': { categoria: 'INV_EQUIPAMENTO', subcategoria: 'Esmag' },
  'IG*GRANDCHEF': { categoria: 'INV_EQUIPAMENTO', subcategoria: 'GrandChef' },

  // Consorcio
  'CONSORCIO EXATA': { categoria: 'FIX_ADMIN', subcategoria: 'Consorcio' },

  // Pagamentos diversos (possivel pessoal ou fornecedor)
  'AMAZON': { categoria: 'A_CATEGORIZAR', subcategoria: 'Amazon - Verificar' },
  'MERCADO DO POLACO': { categoria: 'CPV_INSUMOS', subcategoria: 'Mercado do Polaco' },
  'SAO BENTO DISTRIBUIDO': { categoria: 'CPV_INSUMOS', subcategoria: 'Sao Bento' },
  'VERDURAO HORTIFRUTI': { categoria: 'CPV_INSUMOS', subcategoria: 'Hortifruti' },

  // Associacao
  'ASA*ASSOCIACAO MULHERE': { categoria: 'FIX_ADMIN', subcategoria: 'Associacao' },

  // Manutenção
  'IDEAL ALUMINIO E VIDROS': { categoria: 'FIX_MANUTENCAO', subcategoria: 'Ideal Aluminio' },
  'ERLUK COMERCIO DE MOVEIS': { categoria: 'FIX_MANUTENCAO', subcategoria: 'Erluk' },

  // Dominio
  'NIC. BR': { categoria: 'FIX_SISTEMA', subcategoria: 'Dominio' },

  // Restaurante/Pessoal
  'LIMA E BULLA': { categoria: 'PESSOAL_SOCIO', subcategoria: 'Restaurante' },
  'LENDAS BAR': { categoria: 'PESSOAL_SOCIO', subcategoria: 'Restaurante' },

  // Antecipacao Granito
  'GRANITO S.A. * ANTECIPAÇÃO': { categoria: 'REC_GRANITO_CRED', subcategoria: 'Antecipacao' },

  // Caixinha
  'DEVOLUÇAO': { categoria: 'AJUSTE', subcategoria: 'Devolucao' }
};

// Aplica regras adicionais
function aplicarRegrasAdicionais() {
  console.log('=== CATEGORIZANDO PENDENTES ===\n');

  let categorizados = 0;
  let aindaPendentes = 0;

  for (const lancamento of lancamentosDb.lancamentos) {
    if (lancamento.categoria !== 'A_CATEGORIZAR') continue;

    const desc = lancamento.descricao_original.toUpperCase();
    let encontrado = false;

    for (const [pattern, regra] of Object.entries(regrasAdicionais)) {
      if (desc.includes(pattern.toUpperCase())) {
        if (regra.categoria !== 'A_CATEGORIZAR') {
          lancamento.categoria = regra.categoria;
          lancamento.subcategoria = regra.subcategoria;
          lancamento.notas = `Categorizado automaticamente por regra: ${pattern}`;
          categorizados++;
          encontrado = true;
          console.log(`  ✓ ${lancamento.id}: ${regra.categoria} (${pattern})`);
        }
        break;
      }
    }

    if (!encontrado) {
      aindaPendentes++;
    }
  }

  // Atualiza lista de pendentes
  pendentesDb.pendentes = pendentesDb.pendentes.filter(p => {
    const lancamento = lancamentosDb.lancamentos.find(l => l.id === p.lancamento_id);
    return lancamento && lancamento.categoria === 'A_CATEGORIZAR';
  });

  console.log(`\nCategorizados: ${categorizados}`);
  console.log(`Ainda pendentes: ${aindaPendentes}`);

  return { categorizados, aindaPendentes };
}

// Lista pendentes restantes por tipo
function listarPendentes() {
  console.log('\n=== PENDENTES RESTANTES ===\n');

  const pendentes = lancamentosDb.lancamentos.filter(l => l.categoria === 'A_CATEGORIZAR');

  // Agrupa por descricao similar
  const grupos = {};
  for (const p of pendentes) {
    // Simplifica descricao para agrupar
    let chave = p.descricao_original
      .replace(/[0-9]+/g, 'X')
      .replace(/•••\.\d+\.\d+-••/g, 'CPF')
      .replace(/\d+\/\d+-\d+/g, 'CNPJ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 60);

    if (!grupos[chave]) {
      grupos[chave] = { count: 0, valor: 0, exemplos: [] };
    }
    grupos[chave].count++;
    grupos[chave].valor += p.valor;
    if (grupos[chave].exemplos.length < 2) {
      grupos[chave].exemplos.push({ id: p.id, valor: p.valor, data: p.data, descricao: p.descricao_original });
    }
  }

  // Ordena por valor absoluto
  const ordenado = Object.entries(grupos)
    .sort((a, b) => Math.abs(b[1].valor) - Math.abs(a[1].valor));

  for (const [desc, info] of ordenado) {
    console.log(`${desc.slice(0, 50).padEnd(50)} | ${String(info.count).padStart(3)} trans | R$ ${info.valor.toFixed(2)}`);
    for (const ex of info.exemplos) {
      console.log(`    -> ${ex.id}: ${ex.data} R$ ${ex.valor.toFixed(2)}`);
    }
  }
}

// Gera resumo por categoria
function gerarResumoPorCategoria() {
  console.log('\n=== RESUMO POR CATEGORIA ===\n');

  const porCategoria = {};
  for (const l of lancamentosDb.lancamentos) {
    const cat = l.categoria;
    if (!porCategoria[cat]) porCategoria[cat] = { count: 0, valor: 0 };
    porCategoria[cat].count++;
    porCategoria[cat].valor += l.valor;
  }

  // Agrupa por tipo
  const grupos = {
    'RECEITA': [],
    'CPV': [],
    'VARIAVEL': [],
    'FIXO': [],
    'IMPOSTO': [],
    'OPERACIONAL': [],
    'INVESTIMENTO': [],
    'PESSOAL_SOCIO': [],
    'OUTROS': []
  };

  for (const [cat, dados] of Object.entries(porCategoria)) {
    if (cat.startsWith('REC_')) grupos['RECEITA'].push([cat, dados]);
    else if (cat.startsWith('CPV_')) grupos['CPV'].push([cat, dados]);
    else if (cat.startsWith('VAR_')) grupos['VARIAVEL'].push([cat, dados]);
    else if (cat.startsWith('FIX_')) grupos['FIXO'].push([cat, dados]);
    else if (cat.startsWith('IMP_')) grupos['IMPOSTO'].push([cat, dados]);
    else if (cat.startsWith('OP_')) grupos['OPERACIONAL'].push([cat, dados]);
    else if (cat.startsWith('INV_')) grupos['INVESTIMENTO'].push([cat, dados]);
    else if (cat === 'PESSOAL_SOCIO') grupos['PESSOAL_SOCIO'].push([cat, dados]);
    else grupos['OUTROS'].push([cat, dados]);
  }

  let totalReceitas = 0;
  let totalDespesas = 0;

  for (const [grupo, categorias] of Object.entries(grupos)) {
    if (categorias.length === 0) continue;

    console.log(`\n--- ${grupo} ---`);
    let subtotal = 0;
    for (const [cat, dados] of categorias.sort((a, b) => b[1].valor - a[1].valor)) {
      const sinal = dados.valor >= 0 ? '+' : '';
      console.log(`  ${cat.padEnd(25)} ${String(dados.count).padStart(4)} trans  ${sinal}R$ ${dados.valor.toFixed(2)}`);
      subtotal += dados.valor;
    }
    console.log(`  ${'SUBTOTAL'.padEnd(25)} ${' '.padStart(10)} R$ ${subtotal.toFixed(2)}`);

    if (grupo === 'RECEITA') totalReceitas = subtotal;
    if (['CPV', 'VARIAVEL', 'FIXO', 'IMPOSTO', 'PESSOAL_SOCIO', 'INVESTIMENTO'].includes(grupo)) {
      totalDespesas += subtotal;
    }
  }

  console.log('\n=== DRE SIMPLIFICADO ===');
  console.log(`Receita Total:        R$ ${totalReceitas.toFixed(2)}`);
  console.log(`Despesas Totais:      R$ ${Math.abs(totalDespesas).toFixed(2)}`);
  console.log(`Resultado:            R$ ${(totalReceitas + totalDespesas).toFixed(2)}`);
}

// Salva arquivos
function salvar() {
  lancamentosDb.ultima_atualizacao = new Date().toISOString().split('T')[0];
  lancamentosDb.metadata.total_categorizados = lancamentosDb.lancamentos.filter(l => l.categoria !== 'A_CATEGORIZAR').length;
  lancamentosDb.metadata.total_pendentes = lancamentosDb.lancamentos.filter(l => l.categoria === 'A_CATEGORIZAR').length;

  pendentesDb.ultima_atualizacao = new Date().toISOString().split('T')[0];

  writeFileSync(join(DADOS_DIR, 'lancamentos.json'), JSON.stringify(lancamentosDb, null, 2));
  writeFileSync(join(DADOS_DIR, 'pendentes.json'), JSON.stringify(pendentesDb, null, 2));

  console.log('\nDados atualizados salvos.');
}

// Executa
aplicarRegrasAdicionais();
salvar();
listarPendentes();
gerarResumoPorCategoria();
