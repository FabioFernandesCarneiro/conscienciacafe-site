# Gestor Financeiro - Consciência Café

> **Carregar este arquivo** quando quiser trabalhar com finanças do negócio.

---

## Contexto do Negócio

**Consciência Café** é uma empresa de venda de café especial e produtos relacionados em Foz do Iguaçu/PR.

### Canais de Venda
- **iFood**: delivery
- **Granito (maquininha)**: cartão crédito/débito presencial
- **PIX**: vendas diretas
- **Caixinha**: dinheiro presencial

### Modelo Financeiro
- **Sem pró-labore formal**: o lucro líquido é a remuneração dos sócios
- **Pessoal informal**: pagamentos de ajudantes são feitos em dinheiro via caixinha (categoria "extra")
- **Regime**: verificar (provavelmente Simples Nacional)

---

## Estrutura de Pastas

```
Financeiro/
├── extratos/              # Arquivos brutos (OFX, CSV)
│   ├── conta-corrente/    # OFX Nubank conta
│   ├── cartao-credito/    # OFX Nubank cartão
│   └── caixinha/          # CSV controle manual
├── dados/                 # Dados persistentes (JSON)
│   ├── lancamentos.json   # Banco de lançamentos categorizados
│   ├── reconciliacoes.json# Batimentos sangria/boleto
│   └── pendentes.json     # Itens para revisão manual
├── scripts/               # Scripts de processamento
│   ├── processar-extratos.mjs   # Importa e categoriza
│   ├── categorizar-pendentes.mjs# Categorização adicional
│   └── gerar-relatorio.mjs      # Gera DRE e relatórios
├── contexto/
│   ├── categorias.md      # Regras de categorização (DRE)
│   ├── fornecedores.json  # Cadastro de fornecedores
│   ├── config.md          # Configurações gerais
│   └── memoria.md         # Insights acumulados
└── relatorios/
    ├── visao-geral.md     # Dashboard principal
    ├── alertas.md         # Pontos de atenção
    ├── conferencia-trimestre.md  # Relatório de conferência
    └── mensal/            # Fechamentos mensais
```

---

## Estrutura do DRE

```
  Receita de Venda
- CPV (Custos dos Produtos Vendidos)
= LUCRO BRUTO
  Margem Bruta (%)
  Markup

- Despesas Variáveis
  > Frete/Logística
  > Embalagens
  > Taxas de cartão/plataforma

- Despesas Fixas
  > Marketing (Facebook, Google Ads)
  > Pessoal (pagamentos informais via caixinha "extra")
  > Administrativas

= EBITDA

- Investimentos (equipamentos)
- Impostos

= LUCRO LÍQUIDO (= remuneração dos sócios)
```

---

## Regras Importantes

### Categorização "Extra" na Caixinha
- **"extra", "extras", "exra"** = Despesa com Pessoal (pagamentos informais)
- Classificar como `FIX_PESSOAL` no DRE

### Operações Internas (não entram no DRE)
- `Transferência` / `Sangria` = movimentação caixinha → banco
- `Pagamento recebido` = pagamento de fatura
- Não são receita nem despesa, apenas fluxo de caixa

### Despesas Pessoais (separar)
- Academia, Spotify, restaurantes pessoais
- Idealmente usar conta/cartão separado

---

## Comandos Disponíveis

| Comando | Ação |
|---------|------|
| "Processa os extratos novos" | Executa scripts de importação e categorização |
| "Como está o mês?" | Resumo executivo rápido |
| "Monta o DRE de [mês]" | DRE detalhado do período |
| "Compara com mês anterior" | Análise de evolução |
| "Quanto gastei com [categoria]?" | Consulta específica |
| "Atualiza a memória" | Registra insights no memoria.md |
| "Lista pendentes" | Mostra itens não categorizados |
| "Gera relatório" | Executa gerar-relatorio.mjs |

### Scripts de Processamento

```bash
# Importar e categorizar extratos
node Financeiro/scripts/processar-extratos.mjs

# Categorização adicional de pendentes
node Financeiro/scripts/categorizar-pendentes.mjs

# Gerar relatório do trimestre
node Financeiro/scripts/gerar-relatorio.mjs

# Gerar relatório de um mês específico
node Financeiro/scripts/gerar-relatorio.mjs --mes 2025-10
```

---

## Workflow Mensal

1. **Exportar extratos**:
   - Nubank conta corrente → OFX → `extratos/conta-corrente/`
   - Nubank cartão → OFX → `extratos/cartao-credito/`
   - Atualizar `extratos/caixinha/` com novos dados

2. **Pedir análise**: "Processa os extratos novos"

3. **Eu faço**:
   - Leio e categorizo transações
   - Atualizo `visao-geral.md`
   - Crio relatório mensal em `relatorios/mensal/`
   - Registro insights em `memoria.md`
   - Identifico alertas

---

## Arquivos de Referência

Antes de processar, ler:
- `contexto/categorias.md` - regras de classificação
- `contexto/config.md` - fornecedores e configurações
- `contexto/memoria.md` - histórico e insights

Depois de processar, atualizar:
- `relatorios/visao-geral.md` - dashboard
- `relatorios/alertas.md` - pontos de atenção
- `relatorios/mensal/YYYY-MM.md` - fechamento do mês
- `contexto/memoria.md` - novos insights

---

## Dados Atuais (Conferido 29/01/2026)

**Período disponível**: Outubro a Dezembro/2025
**Fontes**: Conta Corrente + Cartão de Crédito + Caixinha
**Lançamentos processados**: 1.267 (100% categorizados)

### DRE Trimestral (Out-Dez/2025)

| Métrica | Trimestre | Média/Mês |
|---------|-----------|-----------|
| Receita Total | R$ 152.180 | **R$ 50.727** |
| CPV | R$ 68.189 (44.8%) | R$ 22.730 |
| **Lucro Bruto** | **R$ 83.991 (55.2%)** | R$ 27.997 |
| Despesas Variáveis | R$ 8.313 | R$ 2.771 |
| Despesas Fixas | R$ 63.807 | R$ 21.269 |
| **EBITDA** | **R$ 11.871 (7.8%)** | **R$ 3.957** |
| Impostos | R$ 3.828 | R$ 1.276 |
| **Lucro Líquido** | **R$ 8.043 (5.3%)** | **R$ 2.681** |

### Fluxo de Caixa (Pós-DRE)

| Item | Valor |
|------|-------|
| Lucro Líquido | R$ 8.043 |
| (-) Aplicações CDB/RDB | R$ 2.000 |
| (-) Retirada Sócios | R$ 2.002 |
| **= Variação Caixa** | **R$ 4.005** |

### Indicadores vs Benchmark

| Indicador | Atual | Benchmark | Status |
|-----------|-------|-----------|--------|
| Margem Bruta | 55.2% | > 50% | OK |
| CPV / Receita | 44.8% | < 40% | Atenção |
| Pessoal / Receita | 20.6% | < 25% | OK |
| Margem EBITDA | 7.8% | > 15% | Atenção |
| Margem Líquida | 5.3% | > 10% | Atenção |

### Estrutura de Receita

| Canal | Valor/Trim | % |
|-------|------------|---|
| PIX | R$ 49.339 | 32% |
| Granito Crédito | R$ 41.651 | 27% |
| Caixinha | R$ 26.675 | 18% |
| Granito Débito | R$ 17.003 | 11% |
| B2B | R$ 14.855 | 10% |
| iFood | R$ 2.659 | 2% |

### Estrutura de Custos (CPV)

| Item | Valor/Trim | % do CPV |
|------|------------|----------|
| Café | R$ 37.027 | 54% |
| Insumos | R$ 27.442 | 40% |
| Outros | R$ 1.358 | 2% |
| Bebidas | R$ 1.356 | 2% |
| Sorvete | R$ 1.135 | 2% |

### Despesas Fixas Principais

| Item | Valor/Trim | % |
|------|------------|---|
| Pessoal CLT | R$ 14.324 | 22% |
| Pessoal Extra | R$ 13.329 | 21% |
| Aluguel | R$ 13.266 | 21% |
| Marketing | R$ 6.153 | 10% |
| Energia | R$ 5.006 | 8% |
| Admin | R$ 2.988 | 5% |
| VR/Benefícios | R$ 2.010 | 3% |
| FGTS | R$ 1.901 | 3% |
| Manutenção | R$ 1.644 | 3% |
| Contador | R$ 1.120 | 2% |
| Sistemas | R$ 1.103 | 2% |
| Água | R$ 704 | 1% |
| Limpeza | R$ 260 | 0% |

### Alertas ativos

- CPV alto (44.8% - benchmark < 40%)
- Margem EBITDA baixa (7.8% - benchmark > 15%)
- Margem Líquida baixa (5.3% - benchmark > 10%)

### Observações da Conferência

- Dados 100% categorizados e conferidos
- Caixinha filtrado para Out-Dez/2025
- Cartão de crédito inclui compras de Set/2025 (fatura Out)
- Sangrias e depósitos por boleto são operações internas (fora do DRE)
- Retirada de sócios identificada pela diferença sangria vs depósitos
