# Regras de Categorização - Consciência Café

Este arquivo define as regras para classificação automática de transações financeiras,
seguindo a estrutura de DRE (Demonstração de Resultado do Exercício).

---

## Estrutura do DRE

```
  Receita de Venda
- Custos dos Produtos Vendidos (CPV)
= LUCRO BRUTO
  Margem Bruta (%)
  Markup

- Despesas Variáveis
  > Frete/Logística
  > Embalagens
  > Taxas de cartão/plataforma

- Despesas Fixas
  > Marketing
  > Pessoal
  > Administrativas

= EBITDA

- Investimentos
- Impostos

= LUCRO LÍQUIDO
```

---

## 1. RECEITA DE VENDA

### 1.1 Vendas Online
| Padrão | Descrição |
|--------|-----------|
| `IFOOD`, `Depósito recebido - IFOOD` | Vendas iFood |
| `GRANITO S.A. * Crédito` | Maquininha - cartão crédito |
| `GRANITO S.A. * Débito` | Maquininha - cartão débito |

### 1.2 Vendas Diretas (PIX/Transferência)
| Padrão | Descrição |
|--------|-----------|
| `Transferência recebida pelo Pix` | Vendas PIX clientes |
| `Transferência Recebida` | TED de clientes |

### 1.3 Vendas B2B (Empresas)
| Padrão | Descrição |
|--------|-----------|
| `CMS CATY CAFE` | Parceiro/revenda |
| `CHA EXPONENCIAL` | Parceiro chás |
| `Cataratas Park Hotel` | Cliente corporativo |
| `AFD TREINAMENTOS` | Cliente corporativo |

### 1.4 Vendas Caixinha
| Padrão | Descrição |
|--------|-----------|
| `Clientes - Revenda de Mercadoria` | Vendas dinheiro/presencial |

---

## 2. CUSTOS DOS PRODUTOS VENDIDOS (CPV)

### 2.1 Fornecedores de Café (PIX) - PRINCIPAIS
| Padrão | Produto | Valor médio/mês |
|--------|---------|-----------------|
| `Alexandre Alexandrini` | Café (principal) | R$ 9.860 |
| `Altilina Evaristo` | Café | R$ 1.195 |
| `CRISTINA DE ARAUJO TAVARES` | Café | R$ 1.251 |

### 2.2 Fornecedores de Café e Alimentos (Cartão/Boleto)
| Padrão | Produto |
|--------|---------|
| `Casa D'Antonio`, `Casa Dantonio` | Café especial |
| `Oliva Foods`, `Olivafoods` | Produtos alimentícios |
| `Ramondasilva` | Mercadorias |
| `Www.Reidocafe.Com.Br` | Café |
| `Confeitaria Jauense` | Produtos confeitaria |
| `Shopvita Foz do Iguacu` | Produtos diversos |
| `Coliseu` | Mercadorias |
| `Casa Vitoria` | Produtos |
| `Rota Colonial Panifica` | Panificação |

### 2.3 Outros Fornecedores (PIX/Boleto)
| Padrão | Produto |
|--------|---------|
| `Ignacio Francisco Emperador` | Sorvete |
| `DR BAO INDUSTRIA DE BEBIDAS` | Bebidas |
| `OFICINA DO SORVETE` | Sorvete |
| `PEREIRA E FRIGOTTO` | Fornecedor geral |
| `CARLOS EDUARDO.*ARTESA` | Artesanato |
| `GRUPO PEREIRA` | Distribuidor |
| `FRIMESA` | Laticínios |

### 2.4 Supermercado/Distribuidores (Insumos)
| Padrão | Descrição |
|--------|-----------|
| `Superm Consalter` | Insumos principais |
| `Mercado do Polaco` | Compras pequenas |
| `Sao Bento Distribuido` | Distribuidor |

### 2.5 Caixinha
| Padrão | Descrição |
|--------|-----------|
| `Compras de Mercadorias para Revenda` | Mercadorias caixinha |

---

## 3. DESPESAS VARIÁVEIS

### 3.1 Frete e Logística
| Padrão | Descrição |
|--------|-----------|
| `JADLOG LOGISTICA` | Frete entregas (boleto) |
| `Frete` (caixinha) | Frete local |

### 3.2 Embalagens
| Padrão | Descrição |
|--------|-----------|
| `Kromapack` | Embalagens |
| `Embalafoz A`, `Pack Foz Embalagens` | Embalagens |
| `Shopee *Mpembalagensfl` | Embalagens |
| `Mercado*Aldaacessorio` | Acessórios/embalagens |

### 3.3 Taxas de Cartão/Plataforma
| Padrão | Descrição |
|--------|-----------|
| Taxa iFood | ~12% do valor (embutido no repasse) |
| Taxa Granito | ~2-3% do valor (embutido no repasse) |

> **Nota**: As taxas já vêm descontadas nos depósitos. Para cálculo real,
> considerar valor bruto das vendas vs valor recebido.

---

## 4. DESPESAS FIXAS

### 4.1 Marketing
| Padrão | Descrição |
|--------|-----------|
| `Facebk *`, `FACEBK` | Facebook/Instagram Ads |
| `Google Ads` | Google Ads |
| `Mp *360imprimir` | Material impresso |

### 4.2 Pessoal

#### Funcionários CLT (PIX mensal)
| Padrão | Função | Valor médio/mês |
|--------|--------|-----------------|
| `Elaine Campos Alves` | Funcionária | R$ 1.740 |
| `Manuely Martins de Souza` | Funcionária | R$ 1.690 |
| `Jhonathan Raphael Maldonado` | Funcionário | R$ 1.343 |

#### Encargos
| Padrão | Descrição |
|--------|-----------|
| `CEF MATRIZ`, `CAIXA ECONOMICA FEDERAL` | FGTS funcionários |
| `ZOOP BRASIL` | Vale Refeição funcionários |
| `GENUSCLIN` | Medicina do trabalho |

#### Extras (PIX)
| Padrão | Descrição |
|--------|-----------|
| `Ana Carolina Goncalves Ayala` | Extra |
| `Ana Carolina Kobayashi` | Extra |
| `Cesar Augusto Muller Padilha` | Extra |
| `extra`, `extras`, `exra` (caixinha) | Pagamentos informais de ajudantes |

#### Serviços de Limpeza/Manutenção
| Padrão | Descrição |
|--------|-----------|
| `Rosane Godinho da Rosa` | Diarista limpeza |
| `Jose Sergio Feitosa` | Manutenção (faz tudo) |
| `Cleison da Rosa` | Desentupidor |
| `ERLUK COMERCIO DE MOVEIS` | Manutenção móveis |

> **Nota**: Não há pró-labore formal. O lucro líquido é a remuneração dos sócios.

### 4.3 Administrativas
| Padrão | Descrição |
|--------|-----------|
| `Railway` | Hospedagem/infraestrutura |
| `Asa*Associacao Mulhere` | Associação |
| `ON DO REGISTRO CIVIL` | Taxas/documentação |
| Contador | Serviços contábeis |
| `Foz do Iguacu Passagen` | Transporte local |

---

## 5. INVESTIMENTOS (CAPEX)

| Padrão | Descrição |
|--------|-----------|
| `Ig*Grandchef` | Equipamentos cozinha |
| `Esmag Foz` | Equipamentos |
| Móveis, equipamentos | Verificar descrição |

> **Nota**: Compras de equipamentos duráveis são investimentos, não despesas.
> Depreciar ao longo do tempo para cálculo correto.

---

## 6. IMPOSTOS

| Padrão | Descrição |
|--------|-----------|
| `IOF` | Imposto sobre operações financeiras |
| DAS/Simples | Imposto mensal (verificar) |
| ICMS, ISS | Se aplicável |

---

## 7. OPERAÇÕES INTERNAS (Não entram no DRE)

| Padrão | Descrição |
|--------|-----------|
| `Pagamento recebido` | Pagamento fatura cartão |
| `Transferência enviada` | Movimentação entre contas |
| `Transferência` (caixinha) | Sangria para banco |
| `Sangria` (caixinha) | Retirada de caixa |

---

## 8. DESPESAS PESSOAIS (Separar do negócio)

| Padrão | Descrição |
|--------|-----------|
| `Performance Academia` | Academia |
| `Dm*Spotify`, `Dm *Spotify` | Streaming música |
| `Amazon`, `Amazonmktplc*` | Verificar caso a caso |
| `Havan` | Verificar caso a caso |
| `Anacristinatelles` | Pessoal |
| `Republica Argentina` | Restaurante/pessoal |
| `Lima e Bulla` | Pessoal |
| `Verdurao Hortifruti` | Pode ser pessoal |

> **Recomendação**: Usar cartão/conta separada para despesas pessoais.

---

## Notas de Categorização

### Atenção Especial
1. **Amazon**: Pode ser negócio (embalagens, equipamentos) ou pessoal - verificar descrição
2. **Supermercado**: Majoritariamente CPV, mas pode ter itens pessoais misturados
3. **Parcelas**: Considerar o valor total da compra, não apenas a parcela
4. **"Extra" na caixinha**: Categoria genérica - detalhar sempre que possível

### Como Categorizar Novas Transações
1. Verificar o MEMO/descrição da transação
2. Buscar padrões conhecidos neste arquivo
3. Se não encontrar, adicionar nova regra aqui
4. Marcar como `A_CATEGORIZAR` para revisão manual

### Códigos de Categoria (Sistema de Persistência)

**RECEITA**
| Código | Descrição |
|--------|-----------|
| `REC_GRANITO_CRED` | Vendas cartão crédito (Granito) |
| `REC_GRANITO_DEB` | Vendas cartão débito (Granito) |
| `REC_PIX` | Vendas PIX clientes |
| `REC_IFOOD` | Vendas iFood |
| `REC_B2B` | Vendas para empresas |
| `REC_B2B_A_VERIFICAR` | Possível B2B (depósito sem origem) |
| `REC_CAIXINHA` | Vendas dinheiro (caixinha) |

**CPV (Custo dos Produtos Vendidos)**
| Código | Descrição |
|--------|-----------|
| `CPV_CAFE` | Fornecedores de café |
| `CPV_INSUMOS` | Supermercado/insumos gerais |
| `CPV_BEBIDAS` | Bebidas |
| `CPV_SORVETE` | Sorvete |
| `CPV_OUTROS` | Outros fornecedores |

**DESPESAS VARIÁVEIS**
| Código | Descrição |
|--------|-----------|
| `VAR_FRETE` | Frete e logística |
| `VAR_EMBALAGENS` | Embalagens |
| `VAR_TAXAS` | Taxas de cartão/plataforma |

**DESPESAS FIXAS**
| Código | Descrição |
|--------|-----------|
| `FIX_ALUGUEL` | Aluguel |
| `FIX_ENERGIA` | Energia elétrica |
| `FIX_AGUA` | Água |
| `FIX_PESSOAL_CLT` | Funcionários CLT |
| `FIX_PESSOAL_EXTRA` | Extras/ajudantes |
| `FIX_FGTS` | FGTS |
| `FIX_VR` | Vale refeição |
| `FIX_CONTADOR` | Contador |
| `FIX_SISTEMA` | Sistemas (Omie, NotaVarejo, Railway) |
| `FIX_MARKETING` | Marketing (Facebook, Google Ads) |
| `FIX_ADMIN` | Administrativas |
| `FIX_MANUTENCAO` | Manutenção |
| `FIX_LIMPEZA` | Limpeza |

**INVESTIMENTOS**
| Código | Descrição |
|--------|-----------|
| `INV_EQUIPAMENTO` | Equipamentos |

**IMPOSTOS**
| Código | Descrição |
|--------|-----------|
| `IMP_DAS` | DAS Simples Nacional |
| `IMP_DARF` | DARF |
| `IMP_PREFEITURA` | ISS Prefeitura |
| `IMP_IOF` | IOF |

**OPERACIONAL (Não entra no DRE)**
| Código | Descrição |
|--------|-----------|
| `OP_SANGRIA` | Sangria caixinha → conta |
| `OP_PAGAMENTO_FATURA` | Pagamento fatura cartão |
| `OP_TRANSFERENCIA` | Transferência interna |

**OUTROS**
| Código | Descrição |
|--------|-----------|
| `PESSOAL_SOCIO` | Despesas pessoais do sócio |
| `AJUSTE` | Ajustes/diferenças |
| `A_CATEGORIZAR` | Pendente revisão |

---

## 9. Banco de Dados de Lançamentos

Os extratos são processados e persistidos em `Financeiro/dados/`:

- `lancamentos.json` - Todos os lançamentos categorizados
- `reconciliacoes.json` - Batimentos sangria/boleto
- `pendentes.json` - Itens para revisão manual

**Processamento**: Execute `node scripts/processar-extratos.mjs`
**Categorização adicional**: Execute `node scripts/categorizar-pendentes.mjs`
