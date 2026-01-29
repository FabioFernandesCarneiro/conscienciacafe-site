# Alertas Financeiros - Consciência Café

**Última verificação**: 28/01/2026

---

## Alertas Ativos

### Alta Prioridade

| # | Alerta | Detalhes | Ação Sugerida |
|---|--------|----------|---------------|
| 1 | CPV muito alto | 48% da receita (benchmark < 40%) - R$ 23.000/mês | Renegociar com fornecedores, especialmente café |
| 2 | Margem apertada | EBITDA 10%, Resultado 5% - pouca folga | Aumentar preços ou reduzir custos |
| 3 | Custo com pessoal alto | 20% da receita (ideal < 15%) - R$ 9.442/mês | Avaliar necessidade de tantos extras (R$ 3.321/mês) |

### Média Prioridade

| # | Alerta | Detalhes | Ação Sugerida |
|---|--------|----------|---------------|
| 4 | Fluxo de caixa zerado | Entradas ≈ Saídas, sem sobra para reserva | Buscar aumentar receita ou reduzir custos |
| 5 | Dependência de fornecedor | Alexandre Alexandrini = 80% do café (R$ 9.860/mês) | Diversificar ou negociar melhores preços |
| 6 | B2B zerou em dezembro | Nenhuma venda para empresas em dez/25 | Contatar clientes: CMS Caty, Chá Exponencial |

### Baixa Prioridade (Monitorar)

| # | Alerta | Detalhes |
|---|--------|----------|
| 7 | iFood irrelevante | Apenas 2% da receita - avaliar se vale manter |

---

## Alertas Resolvidos

| Data | Alerta | Resolução |
|------|--------|-----------|
| 28/01/2026 | Impostos não contabilizados | Identificados: DAS R$ 647 + DARF R$ 399 + Prefeitura R$ 625 = R$ 1.671/mês |
| 28/01/2026 | CPV desconhecido | Mapeados: PIX R$ 12.467 + Cartão R$ 7.123 + Boletos R$ 2.869 = R$ 23.000/mês (48%) |
| 28/01/2026 | Estrutura de pessoal desconhecida | Mapeados: 3 CLT + FGTS + VR + extras + benefícios = R$ 9.442/mês (20%) |
| 28/01/2026 | Cartão de crédito não detalhado | Processado: R$ 9.971/mês - 100% despesas do negócio |
| 28/01/2026 | Despesas pessoais misturadas | Verificado: todo cartão é do negócio (academia = benefício funcionários) |

---

## Indicadores de Alerta

| Indicador | Valor Atual | Limite | Status |
|-----------|-------------|--------|--------|
| CPV | 48% | < 40% | **ACIMA** |
| Custo Pessoal | 20% | < 15% | Acima |
| Custo Ocupação | 12% | < 15% | OK |
| Margem Bruta | 52% | > 50% | Limite |
| Margem EBITDA | 10% | > 20% | **BAIXO** |
| Margem Líquida | 5% | > 10% | **BAIXO** |
| Fluxo de Caixa | -R$ 386 | > R$ 0 | Atenção |

---

## Configuração de Alertas Automáticos

### Regras Ativas
- Custo pessoal > 15% da receita: ALERTAR
- Marketing > R$ 1.500/mês: ALERTAR
- Fatura cartão > R$ 12.000: ALERTAR
- Receita caixinha < R$ 7.000/mês: ALERTAR
- Novo fornecedor > R$ 500: INFORMAR
- Fluxo de caixa negativo: ALERTAR

### Próxima Verificação
- Quando: Após processamento de Jan/2026
- Foco: Tendência de receita, custo pessoal, B2B

