#!/usr/bin/env node
/**
 * Script de processamento de extratos financeiros
 *
 * Processa arquivos OFX (conta corrente e cartao) e CSV (caixinha)
 * e popula o banco de dados JSON com lancamentos categorizados.
 *
 * Uso: node processar-extratos.mjs
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, basename } from 'path';

// Caminhos
const FINANCEIRO_DIR = join(import.meta.dirname, '..');
const EXTRATOS_DIR = join(FINANCEIRO_DIR, 'extratos');
const DADOS_DIR = join(FINANCEIRO_DIR, 'dados');
const CONTEXTO_DIR = join(FINANCEIRO_DIR, 'contexto');

// Carregar configuracoes
const fornecedores = JSON.parse(readFileSync(join(CONTEXTO_DIR, 'fornecedores.json'), 'utf-8'));

// Estado do banco
let lancamentosDb = JSON.parse(readFileSync(join(DADOS_DIR, 'lancamentos.json'), 'utf-8'));
let reconciliacoesDb = JSON.parse(readFileSync(join(DADOS_DIR, 'reconciliacoes.json'), 'utf-8'));
let pendentesDb = JSON.parse(readFileSync(join(DADOS_DIR, 'pendentes.json'), 'utf-8'));

// Contadores
let stats = {
  total_processados: 0,
  categorizados: 0,
  pendentes: 0,
  duplicados: 0,
  por_fonte: {}
};

/**
 * Gera ID unico para lancamento
 */
function gerarId(fonte, data, index) {
  const prefix = fonte === 'conta-corrente' ? 'cc' :
                 fonte === 'cartao-credito' ? 'cart' : 'cx';
  const dataStr = data.replace(/-/g, '');
  return `${prefix}_${dataStr}_${String(index).padStart(3, '0')}`;
}

/**
 * Verifica se lancamento ja existe (por FITID ou data+valor+descricao)
 */
function lancamentoExiste(fitid, data, valor, descricao) {
  return lancamentosDb.lancamentos.some(l =>
    l.fitid === fitid ||
    (l.data === data && Math.abs(l.valor - valor) < 0.01 && l.descricao_original === descricao)
  );
}

/**
 * Categoriza lancamento baseado em regras
 */
function categorizar(descricao, valor, tipo, fonte) {
  const desc = descricao.toUpperCase();

  // Receitas - Conta Corrente
  if (fonte === 'conta-corrente' && tipo === 'entrada') {
    // iFood
    if (desc.includes('IFOOD')) return { categoria: 'REC_IFOOD', subcategoria: null };

    // Granito
    if (desc.includes('GRANITO') && desc.includes('CRÉDITO')) return { categoria: 'REC_GRANITO_CRED', subcategoria: null };
    if (desc.includes('GRANITO') && desc.includes('DÉBITO')) return { categoria: 'REC_GRANITO_DEB', subcategoria: null };

    // Deposito por Boleto = Sangria do caixinha
    if (desc.includes('DEPÓSITO RECEBIDO POR BOLETO')) return { categoria: 'OP_SANGRIA', subcategoria: 'boleto_caixinha' };

    // B2B
    if (desc.includes('CHA EXPONENCIAL')) return { categoria: 'REC_B2B', subcategoria: 'Cha Exponencial' };
    if (desc.includes('CMS CATY CAFE')) return { categoria: 'REC_B2B', subcategoria: 'CMS Caty Cafe' };
    if (desc.includes('CATARATAS PARK')) return { categoria: 'REC_B2B', subcategoria: 'Cataratas Park Hotel' };
    if (desc.includes('AFD TREINAMENTOS')) return { categoria: 'REC_B2B', subcategoria: 'AFD Treinamentos' };

    // PIX recebido (clientes)
    if (desc.includes('TRANSFERÊNCIA RECEBIDA') || desc.includes('PIX')) {
      // Verificar se nao e de fornecedor/funcionario (pagamento de volta)
      return { categoria: 'REC_PIX', subcategoria: null };
    }
  }

  // Despesas - Conta Corrente (saidas PIX/TED)
  if (fonte === 'conta-corrente' && tipo === 'saida') {
    // Funcionarios CLT
    if (desc.includes('ELAINE CAMPOS ALVES')) return { categoria: 'FIX_PESSOAL_CLT', subcategoria: 'Elaine' };
    if (desc.includes('MANUELY MARTINS')) return { categoria: 'FIX_PESSOAL_CLT', subcategoria: 'Manuely' };
    if (desc.includes('JHONATHAN RAPHAEL')) return { categoria: 'FIX_PESSOAL_CLT', subcategoria: 'Jhonathan' };

    // Extras
    if (desc.includes('ANA CAROLINA GONCALVES AYALA')) return { categoria: 'FIX_PESSOAL_EXTRA', subcategoria: 'Ana Carolina GA' };
    if (desc.includes('ANA CAROLINA KOBAYASHI')) return { categoria: 'FIX_PESSOAL_EXTRA', subcategoria: 'Ana Carolina K' };
    if (desc.includes('CESAR AUGUSTO MULLER')) return { categoria: 'FIX_PESSOAL_EXTRA', subcategoria: 'Cesar' };

    // Limpeza/Manutencao
    if (desc.includes('ROSANE GODINHO')) return { categoria: 'FIX_LIMPEZA', subcategoria: 'Rosane' };
    if (desc.includes('JOSE SERGIO FEITOSA')) return { categoria: 'FIX_MANUTENCAO', subcategoria: 'Jose Sergio' };
    if (desc.includes('CLEISON DA ROSA')) return { categoria: 'FIX_MANUTENCAO', subcategoria: 'Cleison' };

    // Fornecedores Cafe
    if (desc.includes('ALEXANDRE ALEXANDRINI')) return { categoria: 'CPV_CAFE', subcategoria: 'Alexandre' };
    if (desc.includes('ALTILINA EVARISTO')) return { categoria: 'CPV_CAFE', subcategoria: 'Altilina' };
    if (desc.includes('CRISTINA DE ARAUJO')) return { categoria: 'CPV_CAFE', subcategoria: 'Cristina' };

    // Sorvete
    if (desc.includes('IGNACIO FRANCISCO EMPERADOR')) return { categoria: 'CPV_SORVETE', subcategoria: 'Ignacio' };
    if (desc.includes('OFICINA DO SORVETE')) return { categoria: 'CPV_SORVETE', subcategoria: 'Oficina' };

    // Bebidas
    if (desc.includes('DR BAO')) return { categoria: 'CPV_BEBIDAS', subcategoria: 'DR BAO' };

    // Encargos
    if (desc.includes('CEF MATRIZ') || desc.includes('CAIXA ECONOMICA')) return { categoria: 'FIX_FGTS', subcategoria: null };
    if (desc.includes('ZOOP')) return { categoria: 'FIX_VR', subcategoria: null };

    // Frete
    if (desc.includes('JADLOG')) return { categoria: 'VAR_FRETE', subcategoria: 'Jadlog' };

    // Impostos/Taxas
    if (desc.includes('PREFEITURA')) return { categoria: 'IMP_PREFEITURA', subcategoria: null };
    if (desc.includes('ON DO REGISTRO CIVIL')) return { categoria: 'FIX_ADMIN', subcategoria: 'Registro Civil' };

    // Pagamento fatura cartao
    if (desc.includes('PAGAMENTO RECEBIDO') || desc.includes('NU PAGAMENTOS')) {
      if (valor < -5000) return { categoria: 'OP_PAGAMENTO_FATURA', subcategoria: null };
    }

    // iFood beneficios (transferencia para recarga)
    if (desc.includes('IFOOD BENEFICIOS')) return { categoria: 'FIX_VR', subcategoria: 'iFood' };
  }

  // Cartao de Credito
  if (fonte === 'cartao-credito') {
    // Marketing
    if (desc.includes('FACEBK') || desc.includes('FACEBOOK')) return { categoria: 'FIX_MARKETING', subcategoria: 'Facebook Ads' };
    if (desc.includes('GOOGLE ADS')) return { categoria: 'FIX_MARKETING', subcategoria: 'Google Ads' };
    if (desc.includes('360IMPRIMIR')) return { categoria: 'FIX_MARKETING', subcategoria: '360imprimir' };

    // Embalagens
    if (desc.includes('KROMAPACK')) return { categoria: 'VAR_EMBALAGENS', subcategoria: 'Kromapack' };
    if (desc.includes('EMBALAFOZ') || desc.includes('PACK FOZ')) return { categoria: 'VAR_EMBALAGENS', subcategoria: 'Embalafoz' };
    if (desc.includes('MPEMBALAGENS')) return { categoria: 'VAR_EMBALAGENS', subcategoria: 'MP Embalagens' };

    // Fornecedores
    if (desc.includes('CASA D') && desc.includes('ANTONIO')) return { categoria: 'CPV_CAFE', subcategoria: 'Casa DAntonio' };
    if (desc.includes('REIDOCAFE')) return { categoria: 'CPV_CAFE', subcategoria: 'Rei do Cafe' };
    if (desc.includes('OLIVA') && desc.includes('FOOD')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Oliva Foods' };
    if (desc.includes('SHOPVITA')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Shopvita' };
    if (desc.includes('SUPERM CONSALTER') || desc.includes('CONSALTER')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Consalter' };
    if (desc.includes('COLISEU')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Coliseu' };
    if (desc.includes('CASA VITORIA')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Casa Vitoria' };
    if (desc.includes('ROTA COLONIAL')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Rota Colonial' };
    if (desc.includes('CONFEITARIA JAUENSE') || desc.includes('JAUENSE')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Confeitaria Jauense' };
    if (desc.includes('RAMONDASILVA')) return { categoria: 'CPV_OUTROS', subcategoria: 'Ramondasilva' };

    // Sistemas
    if (desc.includes('RAILWAY')) return { categoria: 'FIX_SISTEMA', subcategoria: 'Railway' };

    // Pessoal do socio
    if (desc.includes('SPOTIFY')) return { categoria: 'PESSOAL_SOCIO', subcategoria: 'Spotify' };
    if (desc.includes('PERFORMANCE ACADEMIA')) return { categoria: 'PESSOAL_SOCIO', subcategoria: 'Academia' };
    if (desc.includes('ANACRISTINATELLES')) return { categoria: 'PESSOAL_SOCIO', subcategoria: 'Pessoal' };
    if (desc.includes('LIMA E BULLA')) return { categoria: 'PESSOAL_SOCIO', subcategoria: 'Restaurante' };
    if (desc.includes('REPUBLICA ARGENTINA')) return { categoria: 'PESSOAL_SOCIO', subcategoria: 'Restaurante' };
    if (desc.includes('HAVAN')) return { categoria: 'PESSOAL_SOCIO', subcategoria: 'Havan' };

    // Amazon - verificar caso a caso (pode ser embalagem ou pessoal)
    if (desc.includes('AMAZON')) return { categoria: 'A_CATEGORIZAR', subcategoria: 'Amazon' };

    // Acessorios/Embalagens
    if (desc.includes('ALDAACESSORIO')) return { categoria: 'VAR_EMBALAGENS', subcategoria: 'ML Acessorios' };
  }

  // Caixinha
  if (fonte === 'caixinha') {
    const descLower = descricao.toLowerCase().trim();

    if (descLower.includes('clientes') && descLower.includes('revenda')) return { categoria: 'REC_CAIXINHA', subcategoria: null };
    if (descLower.includes('compras') && descLower.includes('mercadoria')) return { categoria: 'CPV_INSUMOS', subcategoria: 'Caixinha' };
    if (descLower === 'frete') return { categoria: 'VAR_FRETE', subcategoria: 'Caixinha' };
    if (descLower === 'extra' || descLower === 'extras' || descLower === 'exra' || descLower === 'extra ' || descLower === 'extras ') {
      return { categoria: 'FIX_PESSOAL_EXTRA', subcategoria: 'Caixinha' };
    }
    if (descLower === 'transferência' || descLower === 'sangria') return { categoria: 'OP_SANGRIA', subcategoria: 'caixinha_para_banco' };
    if (descLower === 'diferença') return { categoria: 'AJUSTE', subcategoria: null };
  }

  return { categoria: 'A_CATEGORIZAR', subcategoria: null };
}

/**
 * Parseia arquivo OFX e retorna transacoes
 */
function parseOFX(conteudo, arquivo) {
  const transacoes = [];

  // Regex para extrair transacoes
  const stmtTrnRegex = /<STMTTRN>([\s\S]*?)<\/STMTTRN>/g;
  let match;

  while ((match = stmtTrnRegex.exec(conteudo)) !== null) {
    const block = match[1];

    const trnType = block.match(/<TRNTYPE>(\w+)/)?.[1] || '';
    const dtPosted = block.match(/<DTPOSTED>(\d{8})/)?.[1] || '';
    const trnAmt = block.match(/<TRNAMT>(-?[\d.]+)/)?.[1] || '0';
    const fitid = block.match(/<FITID>([^<]+)/)?.[1] || '';
    const memo = block.match(/<MEMO>([^<]+)/)?.[1] || '';

    if (dtPosted && fitid) {
      const data = `${dtPosted.slice(0, 4)}-${dtPosted.slice(4, 6)}-${dtPosted.slice(6, 8)}`;
      const valor = parseFloat(trnAmt);

      transacoes.push({
        data,
        valor: Math.abs(valor),
        tipo: valor >= 0 ? 'entrada' : 'saida',
        descricao: memo.trim(),
        fitid,
        arquivo
      });
    }
  }

  return transacoes;
}

/**
 * Parseia arquivo CSV do caixinha
 */
function parseCSV(conteudo, arquivo) {
  const transacoes = [];
  const linhas = conteudo.split('\n').slice(1); // Pula cabecalho

  for (const linha of linhas) {
    if (!linha.trim() || linha.trim() === ',,,') continue;

    // Parse CSV considerando virgula como separador decimal em alguns casos
    const partes = linha.split(',');
    if (partes.length < 4) continue;

    const data = partes[0].trim();
    const descricao = partes[1].trim();
    let valorStr = partes[2].trim();
    const tipoStr = partes[3].trim().toUpperCase();

    if (!data || !descricao) continue;

    // Converter data DD/MM/YYYY para YYYY-MM-DD
    const dataMatch = data.match(/(\d{2})\/(\d{2})\/(\d{4})/);
    if (!dataMatch) continue;
    const dataISO = `${dataMatch[3]}-${dataMatch[2]}-${dataMatch[1]}`;

    // Converter valor (pode ter virgula como decimal)
    valorStr = valorStr.replace('"', '').replace('"', '').replace(',', '.');
    const valor = Math.abs(parseFloat(valorStr) || 0);

    const tipo = tipoStr.includes('CRÉD') || tipoStr.includes('CRED') ? 'entrada' : 'saida';

    transacoes.push({
      data: dataISO,
      valor,
      tipo,
      descricao,
      fitid: `cx_${dataISO}_${descricao.slice(0, 20)}_${valor}`,
      arquivo
    });
  }

  return transacoes;
}

/**
 * Processa conta corrente
 */
function processarContaCorrente() {
  console.log('\n=== PROCESSANDO CONTA CORRENTE ===\n');

  const dir = join(EXTRATOS_DIR, 'conta-corrente');
  const arquivos = readdirSync(dir).filter(f => f.endsWith('.ofx'));

  let contadorId = lancamentosDb.lancamentos.filter(l => l.fonte === 'conta-corrente').length;

  for (const arquivo of arquivos) {
    console.log(`Processando: ${arquivo}`);
    const conteudo = readFileSync(join(dir, arquivo), 'utf-8');
    const transacoes = parseOFX(conteudo, arquivo);

    stats.por_fonte['conta-corrente'] = stats.por_fonte['conta-corrente'] || { total: 0, processados: 0 };
    stats.por_fonte['conta-corrente'].total += transacoes.length;

    for (const t of transacoes) {
      if (lancamentoExiste(t.fitid, t.data, t.valor, t.descricao)) {
        stats.duplicados++;
        continue;
      }

      const { categoria, subcategoria } = categorizar(t.descricao, t.tipo === 'entrada' ? t.valor : -t.valor, t.tipo, 'conta-corrente');

      const lancamento = {
        id: gerarId('conta-corrente', t.data, ++contadorId),
        fonte: 'conta-corrente',
        arquivo_origem: t.arquivo,
        fitid: t.fitid,
        data: t.data,
        valor: t.tipo === 'entrada' ? t.valor : -t.valor,
        tipo: t.tipo,
        descricao_original: t.descricao,
        categoria,
        subcategoria,
        fornecedor_cliente: subcategoria,
        reconciliado: false,
        reconciliado_com: null,
        notas: null,
        processado_em: new Date().toISOString().split('T')[0]
      };

      lancamentosDb.lancamentos.push(lancamento);
      stats.total_processados++;
      stats.por_fonte['conta-corrente'].processados++;

      if (categoria === 'A_CATEGORIZAR') {
        pendentesDb.pendentes.push({
          lancamento_id: lancamento.id,
          descricao: t.descricao,
          valor: lancamento.valor,
          data: t.data,
          sugestoes: []
        });
        stats.pendentes++;
      } else {
        stats.categorizados++;
      }
    }

    if (!lancamentosDb.metadata.fontes_processadas.includes(arquivo)) {
      lancamentosDb.metadata.fontes_processadas.push(arquivo);
    }
  }
}

/**
 * Processa cartao de credito
 */
function processarCartaoCredito() {
  console.log('\n=== PROCESSANDO CARTAO DE CREDITO ===\n');

  const dir = join(EXTRATOS_DIR, 'cartao-credito');
  const arquivos = readdirSync(dir).filter(f => f.endsWith('.ofx'));

  let contadorId = lancamentosDb.lancamentos.filter(l => l.fonte === 'cartao-credito').length;

  for (const arquivo of arquivos) {
    console.log(`Processando: ${arquivo}`);
    const conteudo = readFileSync(join(dir, arquivo), 'utf-8');
    const transacoes = parseOFX(conteudo, arquivo);

    stats.por_fonte['cartao-credito'] = stats.por_fonte['cartao-credito'] || { total: 0, processados: 0 };
    stats.por_fonte['cartao-credito'].total += transacoes.length;

    for (const t of transacoes) {
      if (lancamentoExiste(t.fitid, t.data, t.valor, t.descricao)) {
        stats.duplicados++;
        continue;
      }

      // Cartao: tudo e saida (despesa)
      const { categoria, subcategoria } = categorizar(t.descricao, -t.valor, 'saida', 'cartao-credito');

      const lancamento = {
        id: gerarId('cartao-credito', t.data, ++contadorId),
        fonte: 'cartao-credito',
        arquivo_origem: t.arquivo,
        fitid: t.fitid,
        data: t.data,
        valor: -t.valor, // Cartao sempre negativo
        tipo: 'saida',
        descricao_original: t.descricao,
        categoria,
        subcategoria,
        fornecedor_cliente: subcategoria,
        reconciliado: false,
        reconciliado_com: null,
        notas: null,
        processado_em: new Date().toISOString().split('T')[0]
      };

      lancamentosDb.lancamentos.push(lancamento);
      stats.total_processados++;
      stats.por_fonte['cartao-credito'].processados++;

      if (categoria === 'A_CATEGORIZAR') {
        pendentesDb.pendentes.push({
          lancamento_id: lancamento.id,
          descricao: t.descricao,
          valor: lancamento.valor,
          data: t.data,
          sugestoes: []
        });
        stats.pendentes++;
      } else {
        stats.categorizados++;
      }
    }

    if (!lancamentosDb.metadata.fontes_processadas.includes(arquivo)) {
      lancamentosDb.metadata.fontes_processadas.push(arquivo);
    }
  }
}

/**
 * Processa caixinha
 */
function processarCaixinha() {
  console.log('\n=== PROCESSANDO CAIXINHA ===\n');

  const dir = join(EXTRATOS_DIR, 'caixinha');
  const arquivos = readdirSync(dir).filter(f => f.endsWith('.csv'));

  let contadorId = lancamentosDb.lancamentos.filter(l => l.fonte === 'caixinha').length;

  for (const arquivo of arquivos) {
    console.log(`Processando: ${arquivo}`);
    const conteudo = readFileSync(join(dir, arquivo), 'utf-8');
    const transacoes = parseCSV(conteudo, arquivo);

    stats.por_fonte['caixinha'] = stats.por_fonte['caixinha'] || { total: 0, processados: 0 };
    stats.por_fonte['caixinha'].total += transacoes.length;

    for (const t of transacoes) {
      if (lancamentoExiste(t.fitid, t.data, t.valor, t.descricao)) {
        stats.duplicados++;
        continue;
      }

      const { categoria, subcategoria } = categorizar(t.descricao, t.tipo === 'entrada' ? t.valor : -t.valor, t.tipo, 'caixinha');

      const lancamento = {
        id: gerarId('caixinha', t.data, ++contadorId),
        fonte: 'caixinha',
        arquivo_origem: t.arquivo,
        fitid: t.fitid,
        data: t.data,
        valor: t.tipo === 'entrada' ? t.valor : -t.valor,
        tipo: t.tipo,
        descricao_original: t.descricao,
        categoria,
        subcategoria,
        fornecedor_cliente: null,
        reconciliado: false,
        reconciliado_com: null,
        notas: null,
        processado_em: new Date().toISOString().split('T')[0]
      };

      lancamentosDb.lancamentos.push(lancamento);
      stats.total_processados++;
      stats.por_fonte['caixinha'].processados++;

      if (categoria === 'A_CATEGORIZAR') {
        pendentesDb.pendentes.push({
          lancamento_id: lancamento.id,
          descricao: t.descricao,
          valor: lancamento.valor,
          data: t.data,
          sugestoes: []
        });
        stats.pendentes++;
      } else {
        stats.categorizados++;
      }
    }

    if (!lancamentosDb.metadata.fontes_processadas.includes(arquivo)) {
      lancamentosDb.metadata.fontes_processadas.push(arquivo);
    }
  }
}

/**
 * Reconcilia transferencias caixinha com depositos por boleto
 */
function reconciliarSangrias() {
  console.log('\n=== RECONCILIANDO SANGRIAS ===\n');

  // Pegar depositos por boleto (conta corrente)
  const depositosBoleto = lancamentosDb.lancamentos.filter(l =>
    l.fonte === 'conta-corrente' &&
    l.categoria === 'OP_SANGRIA' &&
    l.subcategoria === 'boleto_caixinha' &&
    !l.reconciliado
  );

  // Pegar transferencias caixinha
  const transferenciasCaixinha = lancamentosDb.lancamentos.filter(l =>
    l.fonte === 'caixinha' &&
    l.categoria === 'OP_SANGRIA' &&
    !l.reconciliado
  );

  console.log(`Depositos por boleto pendentes: ${depositosBoleto.length}`);
  console.log(`Transferencias caixinha pendentes: ${transferenciasCaixinha.length}`);

  let reconciliados = 0;
  let recId = reconciliacoesDb.reconciliacoes.length;

  for (const deposito of depositosBoleto) {
    const dataDeposito = new Date(deposito.data);
    const valorDeposito = deposito.valor;

    // Buscar transferencia proxima (+-3 dias, valor +-50)
    const candidatos = transferenciasCaixinha.filter(t => {
      if (t.reconciliado) return false;

      const dataTransf = new Date(t.data);
      const diffDias = Math.abs((dataDeposito - dataTransf) / (1000 * 60 * 60 * 24));
      const diffValor = Math.abs(valorDeposito - Math.abs(t.valor));

      return diffDias <= 3 && diffValor <= 50;
    });

    if (candidatos.length > 0) {
      // Pegar o mais proximo em valor
      const melhor = candidatos.reduce((a, b) =>
        Math.abs(valorDeposito - Math.abs(a.valor)) < Math.abs(valorDeposito - Math.abs(b.valor)) ? a : b
      );

      // Criar reconciliacao
      const rec = {
        id: `rec_${String(++recId).padStart(3, '0')}`,
        data: deposito.data,
        tipo: 'sangria_caixinha',
        lancamento_conta: deposito.id,
        lancamento_caixinha: melhor.id,
        valor_conta: deposito.valor,
        valor_caixinha: melhor.valor,
        diferenca: deposito.valor - Math.abs(melhor.valor),
        status: Math.abs(deposito.valor - Math.abs(melhor.valor)) < 1 ? 'ok' : 'diferenca'
      };

      reconciliacoesDb.reconciliacoes.push(rec);

      // Marcar como reconciliado
      deposito.reconciliado = true;
      deposito.reconciliado_com = melhor.id;
      melhor.reconciliado = true;
      melhor.reconciliado_com = deposito.id;

      reconciliados++;
    }
  }

  // Depositos nao reconciliados = possivel B2B
  const depositosNaoReconciliados = depositosBoleto.filter(d => !d.reconciliado);
  if (depositosNaoReconciliados.length > 0) {
    console.log(`\nDepositos por boleto NAO reconciliados (possivel B2B):`);
    for (const d of depositosNaoReconciliados) {
      console.log(`  ${d.data}: R$ ${d.valor.toFixed(2)}`);
      d.categoria = 'REC_B2B_A_VERIFICAR';
      d.notas = 'Deposito por boleto sem correspondencia no caixinha - verificar se e B2B';
    }
  }

  // Transferencias nao reconciliadas = problema no caixinha
  const transferenciasNaoReconciliadas = transferenciasCaixinha.filter(t => !t.reconciliado);
  if (transferenciasNaoReconciliadas.length > 0) {
    console.log(`\nTransferencias caixinha NAO reconciliadas:`);
    for (const t of transferenciasNaoReconciliadas) {
      console.log(`  ${t.data}: R$ ${Math.abs(t.valor).toFixed(2)}`);
      t.notas = 'Transferencia sem deposito correspondente na conta - verificar';
    }
  }

  // Atualizar resumo
  reconciliacoesDb.resumo.total_reconciliados = reconciliados;
  reconciliacoesDb.resumo.total_pendentes = depositosNaoReconciliados.length + transferenciasNaoReconciliadas.length;
  reconciliacoesDb.resumo.soma_reconciliada = reconciliacoesDb.reconciliacoes.reduce((s, r) => s + r.valor_conta, 0);

  console.log(`\nTotal reconciliado: ${reconciliados}`);
}

/**
 * Gera relatorio de conferencia
 */
function gerarRelatorioConferencia() {
  console.log('\n========================================');
  console.log('       RELATORIO DE CONFERENCIA        ');
  console.log('========================================\n');

  console.log('PROCESSAMENTO:');
  console.log(`  Total processados: ${stats.total_processados}`);
  console.log(`  Categorizados: ${stats.categorizados}`);
  console.log(`  Pendentes: ${stats.pendentes}`);
  console.log(`  Duplicados (ignorados): ${stats.duplicados}`);

  console.log('\nPOR FONTE:');
  for (const [fonte, dados] of Object.entries(stats.por_fonte)) {
    console.log(`  ${fonte}:`);
    console.log(`    Total no arquivo: ${dados.total}`);
    console.log(`    Processados: ${dados.processados}`);
  }

  // Totais por categoria
  console.log('\nTOTAIS POR CATEGORIA:');
  const porCategoria = {};
  for (const l of lancamentosDb.lancamentos) {
    const cat = l.categoria;
    if (!porCategoria[cat]) porCategoria[cat] = { count: 0, valor: 0 };
    porCategoria[cat].count++;
    porCategoria[cat].valor += l.valor;
  }

  const categorias = Object.entries(porCategoria).sort((a, b) => b[1].valor - a[1].valor);
  for (const [cat, dados] of categorias) {
    const sinal = dados.valor >= 0 ? '+' : '';
    console.log(`  ${cat.padEnd(25)} ${String(dados.count).padStart(4)} trans  ${sinal}R$ ${dados.valor.toFixed(2)}`);
  }

  // Resumo receita x despesa
  const receitas = lancamentosDb.lancamentos
    .filter(l => l.categoria.startsWith('REC_'))
    .reduce((s, l) => s + l.valor, 0);
  const despesas = lancamentosDb.lancamentos
    .filter(l => !l.categoria.startsWith('REC_') && !l.categoria.startsWith('OP_') && l.valor < 0)
    .reduce((s, l) => s + l.valor, 0);

  console.log('\nRESUMO FINANCEIRO:');
  console.log(`  Receitas: R$ ${receitas.toFixed(2)}`);
  console.log(`  Despesas: R$ ${Math.abs(despesas).toFixed(2)}`);
  console.log(`  Resultado: R$ ${(receitas + despesas).toFixed(2)}`);

  // Reconciliacao
  console.log('\nRECONCILIACAO SANGRIAS:');
  console.log(`  Reconciliados: ${reconciliacoesDb.resumo.total_reconciliados}`);
  console.log(`  Pendentes: ${reconciliacoesDb.resumo.total_pendentes}`);
  console.log(`  Valor reconciliado: R$ ${reconciliacoesDb.resumo.soma_reconciliada.toFixed(2)}`);
}

/**
 * Salva bancos de dados
 */
function salvar() {
  lancamentosDb.ultima_atualizacao = new Date().toISOString().split('T')[0];
  lancamentosDb.metadata.total_processado = lancamentosDb.lancamentos.length;
  lancamentosDb.metadata.total_categorizados = lancamentosDb.lancamentos.filter(l => l.categoria !== 'A_CATEGORIZAR').length;
  lancamentosDb.metadata.total_pendentes = lancamentosDb.lancamentos.filter(l => l.categoria === 'A_CATEGORIZAR').length;

  reconciliacoesDb.ultima_atualizacao = new Date().toISOString().split('T')[0];
  pendentesDb.ultima_atualizacao = new Date().toISOString().split('T')[0];

  writeFileSync(join(DADOS_DIR, 'lancamentos.json'), JSON.stringify(lancamentosDb, null, 2));
  writeFileSync(join(DADOS_DIR, 'reconciliacoes.json'), JSON.stringify(reconciliacoesDb, null, 2));
  writeFileSync(join(DADOS_DIR, 'pendentes.json'), JSON.stringify(pendentesDb, null, 2));

  console.log('\nDados salvos em:');
  console.log(`  ${join(DADOS_DIR, 'lancamentos.json')}`);
  console.log(`  ${join(DADOS_DIR, 'reconciliacoes.json')}`);
  console.log(`  ${join(DADOS_DIR, 'pendentes.json')}`);
}

// Executar
console.log('===========================================');
console.log('  PROCESSADOR DE EXTRATOS FINANCEIROS     ');
console.log('  Consciencia Cafe                        ');
console.log('===========================================');

processarContaCorrente();
processarCartaoCredito();
processarCaixinha();
reconciliarSangrias();
salvar();
gerarRelatorioConferencia();
