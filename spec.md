# Plano: Consciência Café - Sistema de Frente de Loja + CRM

## Contexto do Projeto

### Problema Central
Sistema POS atual (versão 3.5.3) é "comanda-first" - barista seleciona Comanda 1-40 ANTES de identificar cliente. "Procurar cliente" aparece depois como campo opcional, resultando em pedidos sem vínculo ao cliente.

**O que queremos:** Sistema "customer-first" onde o diferencial competitivo vem dos **dados e insights acumulados** sobre cada cliente ao longo do tempo.

### Sistema Atual (Análise dos Prints)
- 746 produtos cadastrados (incluindo livros de consciência)
- Faturamento ~R$40k/mês
- Top 5 clientes já rastreados
- **Setor de preparo** define impressora (Bebidas/Comidas)
- **Cardápios** permite preços por canal - usar para B2B!
- **Prestador** em cada pedido (comissões)
- Comandas numeradas 1-40 em grid

### Requisitos Chave Descobertos
1. **Interface 100% no celular do barista** - cliente não mexe no celular
2. **Customer-first, não comanda-first** - identificar cliente ANTES de abrir pedido
3. **Real-time sync** - 3-5 baristas editando mesmo pedido simultaneamente
4. **Impressora térmica** - substituir sistema POS atual, imprimir direto do novo app
5. **PWA preferido** - web com cache, sem app store, updates instantâneos
6. **WhatsApp como canal principal** - CRM com interface de funis, automação
7. **Setor de preparo** - manter separação Bebidas/Comidas para impressão

### Fluxo Atual vs Novo

**ATUAL (comanda-first):**
```
Barista seleciona Comanda 1 →
[Opcionalmente] Procura cliente →
Adiciona produtos →
Seleciona prestador →
Envia pedido → Imprime
```

**NOVO (customer-first):**
```
Cliente chega → Barista pergunta nome/telefone →
Sistema mostra: último pedido, preferências, cashback →
Se B2B: pergunta empresa, aplica preços B2B →
Barista registra pedido vinculado →
Pedido imprime dividido (bebidas/comidas) →
Pagamento no caixa ou maquininha →
Cashback creditado automaticamente →
WhatsApp: agradecimento + saldo
```

---

## Decisão Técnica: Stack Recomendado

### Frontend: PWA com Next.js 14
**Por quê não Flutter:**
- Requisito de updates instantâneos (PWA > app store)
- Uso em celular via browser é suficiente
- Easier to maintain, single codebase
- Offline-first via Service Worker

**Estrutura:**
```
apps/
├── cafe/                    # PWA frente de loja (Next.js)
│   ├── app/
│   │   ├── (barista)/      # Interface barista
│   │   ├── (caixa)/        # Interface caixa
│   │   └── (admin)/        # Dashboard gestão
│   └── lib/
│       ├── hooks/
│       └── components/
├── whatsapp-crm/           # Interface CRM WhatsApp
└── financeiro/ → gestao/   # Renomear: OKRs, B2B, Financeiro, Dashboards
```

### Backend: Firebase Realtime Database
**Por quê:**
- Real-time sync nativo (múltiplos baristas)
- Já conhece Firebase (intellicoffee)
- Escalável, sem servidor para manter
- Offline-first built-in

### WhatsApp: Baileys + Custom CRM UI
**Por quê build from scratch:**
- Controle total do fluxo
- Interface CRM customizada (funis B2B, B2C)
- Sem custos de API oficial para volume inicial
- Automações personalizadas

---

## MVP 30 Dias: Pedido Rápido + CRM

### Escopo MVP
1. **Cadastro de Cliente** (nome + telefone)
2. **Visualização de Cliente** (último pedido, preferências, pontos)
3. **Registro de Pedido** vinculado ao cliente
4. **Impressão** via Web Print API (substituir POS atual)
5. **Fechamento de Conta** com crédito de pontos
6. **Fechamento de Caixa** (ver seção específica abaixo)
7. **Notificação WhatsApp** pós-venda (saldo de pontos)

### Fora do MVP
- App do cliente
- Automações WhatsApp complexas
- Jornada de descoberta de café
- Integração B2B completa

---

## Estrutura de Dados (Firebase)

```typescript
// customers/{customerId}
{
  name: string,
  phone: string,
  type: 'b2c' | 'b2b',
  companyName?: string,       // Se B2B
  createdAt: Timestamp,
  lastVisit: Timestamp,
  totalVisits: number,
  totalSpent: number,
  preferences: {
    favoriteOrder: string,
    sensoryProfile: {...},    // Para futuro
  },
  loyalty: {
    points: number,
    tier: 'bronze' | 'silver' | 'gold',
    history: [{date, points, reason}]
  }
}

// orders/{orderId}
{
  customerId: string,
  customerName: string,       // Denormalized para real-time
  status: 'open' | 'preparing' | 'ready' | 'paid',
  items: [{
    productId: string,
    name: string,
    price: number,
    quantity: number,
    station: 'bebidas' | 'comidas',
    notes: string
  }],
  payments: [{method, amount}],
  baristaId: string,
  createdAt: Timestamp,
  paidAt: Timestamp
}

// products/{productId}
{
  name: string,
  description: string,
  category: string,              // "Bebidas Quentes", "Cafés Filtrados", etc.
  type: 'produto' | 'servico',
  unit: 'UN' | 'KG' | etc,

  // Setor define impressora destino
  station: 'bebidas' | 'comidas',
  stockSection: string,

  // Preços por canal (inspirado no sistema atual "Cardápios")
  prices: {
    balcao: number,             // Preço padrão B2C
    b2b: number,                // Preço para empresas
    delivery: number            // Se tiver delivery próprio
  },

  // Produção
  productionCost: number,
  prepTime: number,              // Minutos

  // Flags
  divisible: boolean,
  autoWeight: boolean,
  isIngredient: boolean,
  chargeCommission: boolean,
  printAsTicket: boolean,

  // Estoque
  stock: number,
  minStock: number,
  maxStock: number,

  // Visual
  images: string[],
  code: string,                  // Código interno
  abbreviation: string,

  active: boolean
}
```

---

## Fechamento de Caixa

### Funcionalidade Crítica
Baseado nos prints do sistema atual, o fechamento de caixa é bem completo e precisa ser replicado.

### Operações de Caixa (Menu Lateral)
1. **Fechar caixa** - Processo de conferência e fechamento
2. **Inserir dinheiro** - Fundo de caixa, reforço (origem + carteira destino)
3. **Retirar dinheiro** - Com motivo, classificação, opção "registrar como despesa"
4. **Realizar sangria** - Transferência para "Caixa da empresa"
5. **Movimentações dos Caixas** - Histórico de todos os fechamentos

### Fluxo de Fechamento
```
1. Lista formas de pagamento com valores do sistema:
   - Dinheiro, Crédito, Débito, PIX, Giftcard, Marketplace
2. Operador informa valor CONFERIDO para cada forma
3. Opção de contagem de cédulas e moedas (expandível)
4. Campo de observação
5. Sistema calcula diferença (Líquido vs Conferido)
6. Relatório gerado com estatísticas
```

### Relatório de Fechamento (dados a mostrar)
**Cabeçalho:**
- Caixa (ex: "Caixa 1"), Status, Movimentação #
- Abertura: data/hora + operador
- Fechamento: data/hora + operador

**Vendas:**
| Campo | Exemplo |
|-------|---------|
| Comanda | R$2.248,35 |
| Produtos | R$2.256,00 |
| Comissão | R$0,00 |
| Serviços | R$0,00 |
| Descontos | -R$7,65 |
| **Total** | R$2.248,35 |

**Entradas de Vendas (por forma de pagamento):**
- Dinheiro, Crédito, PIX, Débito, Giftcard, Marketplace

**Outras Operações:**
- Entradas (fundo de caixa, reforços)
- Saídas (sangrias, despesas)
- Receitas

**Conferência de Caixa:**
| Descrição | Líquido | Conferido | Diferença |
|-----------|---------|-----------|-----------|
| Dinheiro | R$230,70 | R$232,00 | R$1,30 |
| Crédito | R$410,00 | R$410,00 | R$0,00 |
| ... | ... | ... | ... |

**Estatísticas:**
- Total de pedidos
- Pedidos cancelados
- Itens cancelados
- Ticket médio
- Tempo médio de atendimento
- Média de produtos por pedido

**Entradas e Saídas Detalhadas:**
| Motivo | Tipo | Valor |
|--------|------|-------|
| Fundo de caixa | Transferência | R$500,00 |
| Sangria | Transferência | -R$1.200,00 |
| extra | Despesa | -R$130,00 |

### Estrutura Firebase
```typescript
// cashRegisters/{registerId}
{
  number: number,                    // Ex: "Caixa 1"
  movementId: string,                // Ex: "#1476772"
  status: 'open' | 'closed',

  openedBy: string,
  openedAt: Timestamp,
  closedBy: string,
  closedAt: Timestamp,

  // Vendas por tipo
  sales: {
    comanda: number,
    products: number,
    commission: number,
    services: number,
    discounts: number,
    total: number
  },

  // Entradas por forma de pagamento
  payments: {
    cash: { expected: number, counted: number, difference: number },
    credit: { expected: number, counted: number, difference: number },
    debit: { expected: number, counted: number, difference: number },
    pix: { expected: number, counted: number, difference: number },
    giftcard: { expected: number, counted: number, difference: number },
    marketplace: { expected: number, counted: number, difference: number }
  },

  // Outras operações
  operations: [{
    type: 'insert' | 'withdraw' | 'sangria',
    amount: number,
    reason: string,
    classification: string,          // Para retiradas
    destination: string,             // Carteira destino
    isExpense: boolean,              // Registrar como despesa
    isRevenue: boolean,              // Registrar como receita
    createdAt: Timestamp,
    createdBy: string
  }],

  // Estatísticas (calculadas)
  stats: {
    totalOrders: number,
    canceledOrders: number,
    canceledItems: number,
    averageTicket: number,
    averageTime: number,             // Em minutos
    averageProducts: number
  },

  notes: string
}
```

### Impressão CUPOM
- Botão "CUPOM" no relatório gera impressão térmica
- Formato resumido para conferência rápida

---

## Fluxo de Pedidos (Nova UI)

### Tela Principal do Barista
```
┌─────────────────────────────────────────────────────┐
│  🔍 [Buscar cliente por nome ou telefone...]        │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  PEDIDOS ATIVOS (3)                    [+ Novo]     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ João Silva  │ │ Maria...    │ │ Cliente     │   │
│  │ 2 itens     │ │ 5 itens     │ │ Anônimo     │   │
│  │ R$ 45,00    │ │ R$ 89,00    │ │ R$ 12,00    │   │
│  │ ⏱ 5min      │ │ ⏱ 12min     │ │ ⏱ 2min      │   │
│  │ 🟢 Fabio    │ │ 🟢 Ana      │ │ 🟢 Fabio    │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Ao Buscar/Selecionar Cliente
```
┌─────────────────────────────────────────────────────┐
│  ← João Silva                      🏢 B2B? [toggle] │
│  ─────────────────────────────────────────────────  │
│  📞 (45) 99999-1234                                 │
│  💰 Cashback: R$ 23,50 disponível                   │
│  ⭐ Nível: Habitué (8 visitas/mês)                  │
│  ─────────────────────────────────────────────────  │
│  ÚLTIMO PEDIDO (3 dias atrás):                      │
│  • Flat White                                       │
│  • Avocado Toast                                    │
│  [🔄 Repetir pedido]                                │
│  ─────────────────────────────────────────────────  │
│  PREFERÊNCIAS:                                      │
│  • Sempre pede leite de aveia                       │
│  • Gosta de cafés frutados                          │
│  ─────────────────────────────────────────────────  │
│           [INICIAR NOVO PEDIDO]                     │
└─────────────────────────────────────────────────────┘
```

### Seleção de Produtos (Similar ao atual, mas melhorado)
```
┌─────────────────────────────────────────────────────┐
│  Pedido: João Silva                    ⏱ 27s       │
│  ─────────────────────────────────────────────────  │
│  [Pães] [☕ Filtrados] [Espressos] [Quentes] [>]    │
│  ─────────────────────────────────────────────────  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 🖼️       │ │ 🖼️       │ │ 🖼️       │           │
│  │Flat White│ │Cappuccino│ │ Latte    │           │
│  │ R$15,00  │ │ R$14,00  │ │ R$13,00  │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ─────────────────────────────────────────────────  │
│  CARRINHO:                                          │
│  • 1x Flat White ................ R$ 15,00         │
│  • 1x Avocado Toast (s/ cebola).. R$ 25,00         │
│  ─────────────────────────────────────────────────  │
│  Prestador: [Fabio ▼]           Total: R$ 40,00    │
│           [ENVIAR PARA PREPARO]                     │
└─────────────────────────────────────────────────────┘
```

### Funcionalidades a Manter do Sistema Atual
1. **Menu de contexto da comanda:**
   - Vincular a mesa
   - Mudar para outra comanda
   - Juntar comandas
   - Imprimir conta
   - Mudar prestador
   - Cancelar

2. **Adicionar produto:**
   - Campo observação (max 255 chars)
   - Seletor de quantidade
   - Editar preço pontualmente

3. **Categorias horizontais** com scroll
4. **Cards de produto** com imagem e preço
5. **Timer** desde abertura do pedido
6. **Prestador** (barista responsável)

### Funcionalidades NOVAS
1. **Cliente como primeiro passo** (obrigatório ou "Cliente Anônimo")
2. **Toggle B2B** para aplicar preços diferenciados
3. **Cashback visível** no perfil do cliente
4. **Último pedido** com botão "Repetir"
5. **Preferências/observações** do cliente
6. **Nível de fidelidade** visível

---

## Programa de Fidelidade: Cashback + Experiências

### Objetivo
Fazer o cliente visitar várias vezes no mês. Sistema híbrido: cashback para todos, experiências exclusivas para recorrentes.

### Mecânica Base: Cashback
- **5% de cashback** em todas as compras
- Saldo visível no WhatsApp e no perfil do barista
- Uso: abater no próximo pedido (mínimo R$10 acumulados)

### Níveis para Clientes Recorrentes
| Nível | Critério | Benefício Extra |
|-------|----------|-----------------|
| **Frequente** | 4+ visitas/mês | 7% cashback |
| **Habitué** | 8+ visitas/mês | 10% cashback + convite cupping mensal |
| **Da Casa** | 12+ visitas/mês | 10% cashback + acesso a lotes exclusivos |

### Experiências Exclusivas (não compráveis)
- Cupping privado com novos lotes
- Primeiro a experimentar lançamentos
- Workshop de métodos de preparo
- Visita à torrefação

### Por que esse modelo
- Cashback simples = fácil de entender
- Níveis incentivam frequência (objetivo: várias visitas/mês)
- Experiências criam conexão emocional (incopiáveis por concorrentes)

---

## WhatsApp CRM: Visão

### Interface Tipo CRM
```
┌─────────────────────────────────────────────────────┐
│ 📱 Consciência Café - WhatsApp CRM                  │
├─────────┬───────────────────────────────────────────┤
│ FUNIS   │  Conversa Ativa                          │
│         │  ┌─────────────────────────────────────┐ │
│ 🆕 Novos (12) │  │ João Silva                       │ │
│ 🔄 Ativos (45) │  │ Último pedido: Flat White         │ │
│ 💤 Sumidos (23)│  │ Pontos: 340 grãos                  │ │
│ 🏢 B2B (8)    │  │                                   │ │
│         │  │ [Mensagem...]                       │ │
│ ─────── │  └─────────────────────────────────────┘ │
│ ALERTAS │                                          │
│ ⚠️ 3 sem resposta                                  │
│ 📅 5 follow-ups                                    │
└─────────┴───────────────────────────────────────────┘
```

### Automações Planejadas
1. **Pós-venda:** "Obrigado pela visita! Você tem 340 grãos 🌱"
2. **Sumido 15 dias:** "Sentimos sua falta! Que tal um café?"
3. **Aniversário:** Mensagem personalizada
4. **B2B Mensal:** "Hora de reabastecer?"
5. **Novidade:** "Chegou café novo de [origem]"

---

## Integração B2B (Fase 2)

### Identificação no Balcão
- Barista pergunta: "É para você ou para empresa?"
- Se empresa: campo "Nome da empresa" aparece
- Sistema muda automaticamente para preços B2B
- Cliente é flagado como lead B2B → aparece no funil WhatsApp CRM

### Integração com /apps/gestao (atual financeiro)
- API REST para sincronizar clientes
- Pedido no balcão cria registro no módulo de gestão
- Evita duplicação de dados
- Módulo de Gestão inclui: B2B, OKRs, Financeiro, Dashboards

---

## Arquivos a Criar/Modificar

### Criar
```
apps/cafe/                           # Novo app PWA Next.js
├── package.json
├── next.config.js
├── app/
│   ├── layout.tsx
│   ├── (barista)/
│   │   ├── page.tsx                # Home barista
│   │   ├── cliente/[id]/page.tsx   # Perfil cliente
│   │   └── pedido/[id]/page.tsx    # Edição pedido
│   ├── (caixa)/
│   │   └── page.tsx                # Fechamento
│   └── (admin)/
│       └── page.tsx                # Dashboard
├── components/
│   ├── CustomerSearch.tsx          # Busca cliente
│   ├── OrderCard.tsx               # Card pedido
│   ├── ProductSelector.tsx         # Seletor produtos
│   └── LoyaltyBadge.tsx           # Status fidelidade
└── lib/
    ├── firebase.ts
    ├── hooks/
    │   ├── useCustomer.ts
    │   └── useOrder.ts
    └── types/
```

### Renomear
```
apps/financeiro/ → apps/gestao/
```

---

## Fases de Implementação

### Fase 1: MVP (30 dias)
- [ ] Setup projeto Next.js PWA
- [ ] Firebase: estrutura de dados
- [ ] Busca/cadastro de cliente
- [ ] Criação de pedido vinculado
- [ ] Listagem pedidos ativos (real-time)
- [ ] Fechamento de conta + pontos
- [ ] Fechamento de caixa (abertura, sangrias, relatório)
- [ ] Integração impressora (Web Print API)

### Fase 2: WhatsApp Base (+ 2 semanas)
- [ ] Integração Baileys
- [ ] Notificação pós-venda
- [ ] Interface CRM básica

### Fase 3: B2B + Gestão (+ 2 semanas)
- [ ] Flag cliente B2B
- [ ] Preços diferenciados
- [ ] Integração /apps/gestao

### Fase 4: Fidelidade Avançada (+ 2 semanas)
- [ ] Níveis e multiplicadores
- [ ] Desafios mensais
- [ ] Histórico de jornada

---

## Verificação

### Como testar MVP
1. **Simular atendimento:** Cadastrar cliente, fazer pedido, fechar
2. **Real-time:** Abrir em 2 dispositivos, editar mesmo pedido
3. **Impressão:** Testar Web Print API com impressora térmica
4. **Offline:** Desligar internet, fazer operações, reconectar

### Métricas de Sucesso
- Tempo de cadastro de cliente < 10 segundos
- Tempo de registro de pedido < 30 segundos
- 100% dos pedidos vinculados a cliente (vs. 0% hoje)
- WhatsApp pós-venda enviado em < 5 minutos

---

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Baristas resistirem | Treinamento hands-on, feedback contínuo |
| Impressora não integrar | Fallback: usar sistema atual em paralelo |
| WhatsApp banir número | Usar número secundário para testes |
| Real-time lag | Firebase Realtime tem baixa latência |

---

## Migração de Dados

### Produtos (746 itens)
**Estratégia:** Importar do sistema atual via API ou export CSV
- Mapear categorias existentes
- Configurar preço B2B (inicialmente = preço balcão, ajustar depois)
- Manter código interno e abreviações
- Importar imagens

### Clientes Existentes
- Top customers já identificados no sistema atual
- Importar base existente se disponível
- Começar programa de fidelidade do zero (sem saldo legado)

### Período de Transição
1. **Semana 1-2:** Sistema novo em paralelo, só para cadastro de clientes
2. **Semana 3-4:** Testar pedidos completos em horários de baixo movimento
3. **Semana 5+:** Migração completa, desligar sistema antigo

---

## Próximos Passos Imediatos

1. ✅ Validar plano com você
2. Renomear `/apps/financeiro` → `/apps/gestao`
3. Criar estrutura `/apps/cafe` (Next.js PWA)
4. Configurar Firebase Realtime Database
5. Implementar tela de busca/cadastro de cliente
6. Configurar impressão via Web Print API
