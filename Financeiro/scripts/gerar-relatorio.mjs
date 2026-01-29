#!/usr/bin/env node
/**
 * Script para geração de relatório de conferência financeira
 *
 * Gera relatório detalhado com verificações de integridade,
 * DRE e resumo por período.
 *
 * Uso: node gerar-relatorio.mjs [--mes YYYY-MM]
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const FINANCEIRO_DIR = join(import.meta.dirname, '..');
const DADOS_DIR = join(FINANCEIRO_DIR, 'dados');
const RELATORIOS_DIR = join(FINANCEIRO_DIR, 'relatorios');

const lancamentosDb = JSON.parse(readFileSync(join(DADOS_DIR, 'lancamentos.json'), 'utf-8'));
const reconciliacoesDb = JSON.parse(readFileSync(join(DADOS_DIR, 'reconciliacoes.json'), 'utf-8'));

// Argumentos
const args = process.argv.slice(2);
const mesArg = args.find((a, i) => args[i - 1] === '--mes');

/**
 * Filtra lancamentos por periodo
 */
function filtrarPorPeriodo(lancamentos, inicio, fim) {
  return lancamentos.filter(l => l.data >= inicio && l.data <= fim);
}

/**
 * Agrupa lancamentos por categoria
 */
function agruparPorCategoria(lancamentos) {
  const grupos = {};
  for (const l of lancamentos) {
    const cat = l.categoria;
    if (!grupos[cat]) grupos[cat] = { count: 0, valor: 0, lancamentos: [] };
    grupos[cat].count++;
    grupos[cat].valor += l.valor;
    grupos[cat].lancamentos.push(l);
  }
  return grupos;
}

/**
 * Calcula DRE
 */
function calcularDRE(lancamentos) {
  const porCategoria = agruparPorCategoria(lancamentos);

  // Receitas
  const receitas = {
    granito_cred: porCategoria['REC_GRANITO_CRED']?.valor || 0,
    granito_deb: porCategoria['REC_GRANITO_DEB']?.valor || 0,
    pix: porCategoria['REC_PIX']?.valor || 0,
    ifood: porCategoria['REC_IFOOD']?.valor || 0,
    b2b: (porCategoria['REC_B2B']?.valor || 0) + (porCategoria['REC_B2B_A_VERIFICAR']?.valor || 0),
    caixinha: porCategoria['REC_CAIXINHA']?.valor || 0
  };
  receitas.total = Object.values(receitas).reduce((a, b) => a + b, 0);

  // CPV
  const cpv = {
    cafe: Math.abs(porCategoria['CPV_CAFE']?.valor || 0),
    insumos: Math.abs(porCategoria['CPV_INSUMOS']?.valor || 0),
    bebidas: Math.abs(porCategoria['CPV_BEBIDAS']?.valor || 0),
    sorvete: Math.abs(porCategoria['CPV_SORVETE']?.valor || 0),
    outros: Math.abs(porCategoria['CPV_OUTROS']?.valor || 0)
  };
  cpv.total = Object.values(cpv).reduce((a, b) => a + b, 0);

  // Margem Bruta
  const lucroBruto = receitas.total - cpv.total;
  const margemBruta = receitas.total > 0 ? (lucroBruto / receitas.total) * 100 : 0;

  // Despesas Variaveis
  const variaveis = {
    frete: Math.abs(porCategoria['VAR_FRETE']?.valor || 0),
    embalagens: Math.abs(porCategoria['VAR_EMBALAGENS']?.valor || 0)
  };
  variaveis.total = Object.values(variaveis).reduce((a, b) => a + b, 0);

  // Despesas Fixas
  const fixas = {
    aluguel: Math.abs(porCategoria['FIX_ALUGUEL']?.valor || 0),
    energia: Math.abs(porCategoria['FIX_ENERGIA']?.valor || 0),
    agua: Math.abs(porCategoria['FIX_AGUA']?.valor || 0),
    pessoal_clt: Math.abs(porCategoria['FIX_PESSOAL_CLT']?.valor || 0),
    pessoal_extra: Math.abs(porCategoria['FIX_PESSOAL_EXTRA']?.valor || 0),
    fgts: Math.abs(porCategoria['FIX_FGTS']?.valor || 0),
    vr: Math.abs(porCategoria['FIX_VR']?.valor || 0),
    contador: Math.abs(porCategoria['FIX_CONTADOR']?.valor || 0),
    sistema: Math.abs(porCategoria['FIX_SISTEMA']?.valor || 0),
    marketing: Math.abs(porCategoria['FIX_MARKETING']?.valor || 0),
    admin: Math.abs(porCategoria['FIX_ADMIN']?.valor || 0),
    manutencao: Math.abs(porCategoria['FIX_MANUTENCAO']?.valor || 0),
    limpeza: Math.abs(porCategoria['FIX_LIMPEZA']?.valor || 0)
  };
  fixas.total = Object.values(fixas).reduce((a, b) => a + b, 0);

  // EBITDA
  const ebitda = lucroBruto - variaveis.total - fixas.total;
  const margemEbitda = receitas.total > 0 ? (ebitda / receitas.total) * 100 : 0;

  // Investimentos
  const investimentos = Math.abs(porCategoria['INV_EQUIPAMENTO']?.valor || 0);

  // Impostos
  const impostos = {
    das: Math.abs(porCategoria['IMP_DAS']?.valor || 0),
    inss: Math.abs(porCategoria['IMP_INSS']?.valor || 0),
    iptu: Math.abs(porCategoria['IMP_IPTU']?.valor || 0)
  };
  impostos.total = Object.values(impostos).reduce((a, b) => a + b, 0);

  // Resultado
  const lucroLiquido = ebitda - investimentos - impostos.total;
  const margemLiquida = receitas.total > 0 ? (lucroLiquido / receitas.total) * 100 : 0;

  // Fluxo de Caixa (movimentações não-DRE)
  const fluxoCaixa = {
    // Sangrias do caixinha (saídas do caixinha para banco)
    sangrias: porCategoria['OP_SANGRIA']?.valor || 0,
    // Aplicações financeiras
    aplicacoes: Math.abs(porCategoria['OP_TRANSFERENCIA']?.valor || 0),
    // Pagamento de fatura (não afeta caixa líquido)
    pagamentoFatura: Math.abs(porCategoria['OP_PAGAMENTO_FATURA']?.valor || 0),
    // Despesas pessoais dos sócios
    pessoalSocio: Math.abs(porCategoria['PESSOAL_SOCIO']?.valor || 0)
  };
  // Retirada de lucro = diferença entre sangrias e depósitos (quando sangrias > depósitos)
  // Sangrias são negativas no caixinha, se o valor líquido é negativo, significa retirada
  fluxoCaixa.retiradaLucro = fluxoCaixa.sangrias < 0 ? Math.abs(fluxoCaixa.sangrias) : 0;

  return {
    receitas,
    cpv,
    lucroBruto,
    margemBruta,
    variaveis,
    fixas,
    ebitda,
    margemEbitda,
    investimentos,
    impostos,
    lucroLiquido,
    margemLiquida,
    fluxoCaixa,
    porCategoria
  };
}

/**
 * Formata valor em reais
 */
function formatMoney(valor) {
  return `R$ ${valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Gera relatorio em markdown
 */
function gerarRelatorioMD(periodo, dre, lancamentos) {
  const totalLancamentos = lancamentos.length;
  const categorizados = lancamentos.filter(l => l.categoria !== 'A_CATEGORIZAR').length;
  const pendentes = lancamentos.filter(l => l.categoria === 'A_CATEGORIZAR').length;

  let md = `# Relatório Financeiro - ${periodo}

> Gerado em: ${new Date().toLocaleDateString('pt-BR')}

---

## Verificação de Integridade

| Métrica | Valor |
|---------|-------|
| Total de lançamentos | ${totalLancamentos} |
| Categorizados | ${categorizados} (${((categorizados / totalLancamentos) * 100).toFixed(1)}%) |
| Pendentes | ${pendentes} |
| Reconciliações | ${reconciliacoesDb.reconciliacoes.length} |

---

## DRE - Demonstração do Resultado

### Receita de Vendas

| Canal | Valor |
|-------|-------|
| Granito Crédito | ${formatMoney(dre.receitas.granito_cred)} |
| Granito Débito | ${formatMoney(dre.receitas.granito_deb)} |
| PIX | ${formatMoney(dre.receitas.pix)} |
| iFood | ${formatMoney(dre.receitas.ifood)} |
| B2B | ${formatMoney(dre.receitas.b2b)} |
| Caixinha | ${formatMoney(dre.receitas.caixinha)} |
| **TOTAL RECEITA** | **${formatMoney(dre.receitas.total)}** |

### Custo dos Produtos Vendidos (CPV)

| Item | Valor |
|------|-------|
| Café | ${formatMoney(dre.cpv.cafe)} |
| Insumos | ${formatMoney(dre.cpv.insumos)} |
| Bebidas | ${formatMoney(dre.cpv.bebidas)} |
| Sorvete | ${formatMoney(dre.cpv.sorvete)} |
| Outros | ${formatMoney(dre.cpv.outros)} |
| **TOTAL CPV** | **${formatMoney(dre.cpv.total)}** |

### Lucro Bruto

| | Valor | % |
|---|-------|---|
| **LUCRO BRUTO** | **${formatMoney(dre.lucroBruto)}** | **${dre.margemBruta.toFixed(1)}%** |

### Despesas Variáveis

| Item | Valor |
|------|-------|
| Frete | ${formatMoney(dre.variaveis.frete)} |
| Embalagens | ${formatMoney(dre.variaveis.embalagens)} |
| **TOTAL VARIÁVEIS** | **${formatMoney(dre.variaveis.total)}** |

### Despesas Fixas

| Item | Valor |
|------|-------|
| Aluguel | ${formatMoney(dre.fixas.aluguel)} |
| Energia | ${formatMoney(dre.fixas.energia)} |
| Água | ${formatMoney(dre.fixas.agua)} |
| Pessoal CLT | ${formatMoney(dre.fixas.pessoal_clt)} |
| Pessoal Extra | ${formatMoney(dre.fixas.pessoal_extra)} |
| FGTS | ${formatMoney(dre.fixas.fgts)} |
| Vale Refeição | ${formatMoney(dre.fixas.vr)} |
| Contador | ${formatMoney(dre.fixas.contador)} |
| Sistemas | ${formatMoney(dre.fixas.sistema)} |
| Marketing | ${formatMoney(dre.fixas.marketing)} |
| Admin | ${formatMoney(dre.fixas.admin)} |
| Manutenção | ${formatMoney(dre.fixas.manutencao)} |
| Limpeza | ${formatMoney(dre.fixas.limpeza)} |
| **TOTAL FIXAS** | **${formatMoney(dre.fixas.total)}** |

### EBITDA

| | Valor | % |
|---|-------|---|
| **EBITDA** | **${formatMoney(dre.ebitda)}** | **${dre.margemEbitda.toFixed(1)}%** |

### Investimentos e Impostos

| Item | Valor |
|------|-------|
| Investimentos (CAPEX) | ${formatMoney(dre.investimentos)} |
| DAS Simples | ${formatMoney(dre.impostos.das)} |
| INSS (Folha) | ${formatMoney(dre.impostos.inss)} |
| IPTU | ${formatMoney(dre.impostos.iptu)} |
| **TOTAL IMPOSTOS** | **${formatMoney(dre.impostos.total)}** |

### Resultado Final

| | Valor | % |
|---|-------|---|
| **LUCRO LÍQUIDO** | **${formatMoney(dre.lucroLiquido)}** | **${dre.margemLiquida.toFixed(1)}%** |

---

## Indicadores

| Indicador | Valor | Benchmark |
|-----------|-------|-----------|
| Margem Bruta | ${dre.margemBruta.toFixed(1)}% | > 50% |
| CPV / Receita | ${((dre.cpv.total / dre.receitas.total) * 100).toFixed(1)}% | < 40% |
| Pessoal / Receita | ${(((dre.fixas.pessoal_clt + dre.fixas.pessoal_extra + dre.fixas.fgts + dre.fixas.vr) / dre.receitas.total) * 100).toFixed(1)}% | < 25% |
| Margem EBITDA | ${dre.margemEbitda.toFixed(1)}% | > 15% |
| Margem Líquida | ${dre.margemLiquida.toFixed(1)}% | > 10% |

---

## Fluxo de Caixa (Movimentações não-DRE)

Estas movimentações não afetam o resultado operacional mas impactam o caixa disponível:

| Item | Valor | Observação |
|------|-------|------------|
| Lucro Líquido (DRE) | ${formatMoney(dre.lucroLiquido)} | Resultado operacional |
| (-) Aplicações Financeiras | ${formatMoney(dre.fluxoCaixa.aplicacoes)} | CDB/RDB |
| (-) Retirada de Lucro (Sócios) | ${formatMoney(dre.fluxoCaixa.retiradaLucro)} | Diferença sangrias vs depósitos |
| (-) Despesas Pessoais | ${formatMoney(dre.fluxoCaixa.pessoalSocio)} | Gastos pessoais no cartão empresa |
| **= Variação Caixa Líquida** | **${formatMoney(dre.lucroLiquido - dre.fluxoCaixa.aplicacoes - dre.fluxoCaixa.retiradaLucro - dre.fluxoCaixa.pessoalSocio)}** | Efetivamente disponível |

### Detalhamento Operacional

| Operação | Valor |
|----------|-------|
| Sangrias Caixinha → Banco | ${formatMoney(dre.fluxoCaixa.sangrias)} |
| Pagamentos de Fatura | ${formatMoney(dre.fluxoCaixa.pagamentoFatura)} |

> **Nota:** Sangrias e pagamentos de fatura são movimentações internas (dinheiro trocando de lugar) e não afetam o patrimônio total.

---

## Observações

- Os valores de receita PIX incluem todas as transferências recebidas de clientes
- Sangrias do caixinha para conta corrente são operações internas e não entram no DRE
- Pagamentos de fatura de cartão são operações internas
- Retirada de lucro = sangrias do caixinha que não foram depositadas na conta (retiradas pelos sócios)

`;

  return md;
}

// Executa
console.log('===========================================');
console.log('  GERADOR DE RELATÓRIO FINANCEIRO         ');
console.log('  Consciência Café                        ');
console.log('===========================================\n');

// Determina periodo
let dataInicio, dataFim, nomePeriodo;

if (mesArg) {
  // Mes especifico
  const [ano, mes] = mesArg.split('-');
  dataInicio = `${ano}-${mes}-01`;
  const ultimoDia = new Date(parseInt(ano), parseInt(mes), 0).getDate();
  dataFim = `${ano}-${mes}-${String(ultimoDia).padStart(2, '0')}`;
  nomePeriodo = `${mes}/${ano}`;
} else {
  // Ultimo trimestre disponivel (Out-Dez 2025)
  dataInicio = '2025-10-01';
  dataFim = '2025-12-31';
  nomePeriodo = 'Out-Dez/2025';
}

console.log(`Período: ${nomePeriodo} (${dataInicio} a ${dataFim})\n`);

// Filtra lancamentos do periodo
// Nota: O banco de dados já contém apenas lançamentos do período desejado
// Conta-corrente e cartão já estão filtrados pelos extratos OFX
// Caixinha já foi filtrado na importação
// Então usamos todos os lançamentos disponíveis
const lancamentosPeriodo = lancamentosDb.lancamentos;
console.log(`Lançamentos no período: ${lancamentosPeriodo.length}\n`);

// Calcula DRE
const dre = calcularDRE(lancamentosPeriodo);

// Exibe resumo no console
console.log('=== RESUMO DRE ===\n');
console.log(`Receita Total:    ${formatMoney(dre.receitas.total)}`);
console.log(`(-) CPV:          ${formatMoney(dre.cpv.total)}`);
console.log(`= Lucro Bruto:    ${formatMoney(dre.lucroBruto)} (${dre.margemBruta.toFixed(1)}%)`);
console.log(`(-) Variáveis:    ${formatMoney(dre.variaveis.total)}`);
console.log(`(-) Fixas:        ${formatMoney(dre.fixas.total)}`);
console.log(`= EBITDA:         ${formatMoney(dre.ebitda)} (${dre.margemEbitda.toFixed(1)}%)`);
console.log(`(-) Investimentos:${formatMoney(dre.investimentos)}`);
console.log(`(-) Impostos:     ${formatMoney(dre.impostos.total)}`);
console.log(`= Lucro Líquido:  ${formatMoney(dre.lucroLiquido)} (${dre.margemLiquida.toFixed(1)}%)`);

// Gera relatorio MD
const relatorioMD = gerarRelatorioMD(nomePeriodo, dre, lancamentosPeriodo);
const nomeArquivo = mesArg ? `${mesArg}.md` : 'conferencia-trimestre.md';
writeFileSync(join(RELATORIOS_DIR, nomeArquivo), relatorioMD);

console.log(`\nRelatório salvo em: ${join(RELATORIOS_DIR, nomeArquivo)}`);

// Fluxo de caixa
console.log('\n=== FLUXO DE CAIXA ===\n');
console.log(`Lucro Líquido:        ${formatMoney(dre.lucroLiquido)}`);
console.log(`(-) Aplicações:       ${formatMoney(dre.fluxoCaixa.aplicacoes)}`);
console.log(`(-) Retirada Sócios:  ${formatMoney(dre.fluxoCaixa.retiradaLucro)}`);
console.log(`(-) Despesas Pessoais:${formatMoney(dre.fluxoCaixa.pessoalSocio)}`);
const variacaoCaixa = dre.lucroLiquido - dre.fluxoCaixa.aplicacoes - dre.fluxoCaixa.retiradaLucro - dre.fluxoCaixa.pessoalSocio;
console.log(`= Variação Caixa:     ${formatMoney(variacaoCaixa)}`);

// Calcula medias mensais
console.log('\n=== MÉDIAS MENSAIS ===\n');
const meses = 3; // Out, Nov, Dez
console.log(`Receita média:     ${formatMoney(dre.receitas.total / meses)}/mês`);
console.log(`CPV médio:         ${formatMoney(dre.cpv.total / meses)}/mês`);
console.log(`Despesas médias:   ${formatMoney((dre.variaveis.total + dre.fixas.total) / meses)}/mês`);
console.log(`EBITDA médio:      ${formatMoney(dre.ebitda / meses)}/mês`);
console.log(`Lucro médio:       ${formatMoney(dre.lucroLiquido / meses)}/mês`);
