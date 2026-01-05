# Detalhamento do Módulo Inicial

## Escopo do MVP

O módulo inicial combinará três elementos fundamentais para criar uma base sólida para o sistema customer centric:

1. **CRM Básico**: Cadastro e gestão de clientes
2. **Atendimento**: Registro de pedidos e preferências
3. **Fidelidade Digital**: Substituição do cartão físico

## Modelagem NoSQL (Firestore)

### Coleção: `customers`
```
{
  id: String (auto-gerado),
  name: String,
  phone: String,
  email: String (opcional),
  birthDate: Timestamp (opcional),
  createdAt: Timestamp,
  updatedAt: Timestamp,
  lastVisit: Timestamp,
  visitCount: Number,
  totalSpent: Number,
  averageTicket: Number,
  loyaltyPoints: Number,
  tier: String (regular, bronze, silver, gold),
  notes: String,
  tags: Array<String>,
  allowsMarketing: Boolean,
  source: String (como conheceu a cafeteria),
  status: String (active, inactive)
}
```

### Subcoleção: `customers/{customerId}/preferences`
```
{
  id: String (auto-gerado),
  category: String (coffee, food, service),
  item: String (specific preference),
  rating: Number (1-5),
  notes: String,
  updatedAt: Timestamp
}
```

### Subcoleção: `customers/{customerId}/visits`
```
{
  id: String (auto-gerado),
  date: Timestamp,
  orderIds: Array<String>,
  totalSpent: Number,
  notes: String,
  servedBy: String
}
```

### Coleção: `orders`
```
{
  id: String (auto-gerado),
  customerId: String (opcional, para pedidos identificados),
  customerName: String,
  tableNumber: Number (opcional),
  createdAt: Timestamp,
  completedAt: Timestamp,
  status: String (open, preparing, completed, cancelled),
  total: Number,
  discountAmount: Number,
  finalAmount: Number,
  paymentMethod: String,
  pointsEarned: Number,
  pointsRedeemed: Number,
  type: String (dine-in, takeaway, delivery),
  notes: String,
  servedBy: String
}
```

### Subcoleção: `orders/{orderId}/items`
```
{
  id: String (auto-gerado),
  productId: String,
  productName: String,
  category: String,
  quantity: Number,
  unitPrice: Number,
  totalPrice: Number,
  customizations: Map<String, String>,
  notes: String,
  status: String (pending, preparing, completed)
}
```

### Coleção: `products`
```
{
  id: String (auto-gerado),
  name: String,
  description: String,
  category: String,
  subcategory: String,
  price: Number,
  image: String (URL),
  preparationTime: Number (minutos),
  isActive: Boolean,
  isFeatured: Boolean,
  allergens: Array<String>,
  tags: Array<String>
}
```

### Coleção: `coffeeProducts` (específica para cafés)
```
{
  id: String (auto-gerado),
  productId: String,
  origin: String,
  farm: String,
  altitude: String,
  variety: String,
  processing: String,
  roastDate: Timestamp,
  roastProfile: String,
  batchNumber: String,
  tastingNotes: Array<String>,
  acidity: Number (1-5),
  body: Number (1-5),
  sweetness: Number (1-5),
  recommendedMethods: Array<String>
}
```

### Coleção: `loyaltyRules`
```
{
  id: String (por tipo: drinks, food, etc),
  pointsPerCurrency: Number,
  minimumForRedemption: Number,
  pointsValidityDays: Number,
  tierThresholds: Map<String, Number>,
  tierBenefits: Map<String, Array<String>>,
  specialRules: Array<Map>
}
```

### Coleção: `loyaltyTransactions`
```
{
  id: String (auto-gerado),
  customerId: String,
  orderId: String (opcional),
  date: Timestamp,
  type: String (earn, redeem, expire, adjust),
  points: Number,
  reason: String,
  createdBy: String
}
```

## Funcionalidades Principais

### 1. Gestão de Clientes
- **Cadastro Rápido**: Nome e telefone como dados mínimos
- **Busca Inteligente**: Por nome, telefone ou preferências
- **Perfil Detalhado**: Visualização de histórico, preferências e status de fidelidade
- **Tags e Segmentação**: Categorização flexível de clientes
- **Observações Especiais**: Campo para registro de informações relevantes

### 2. Atendimento e Pedidos
- **Identificação de Cliente**: Associação rápida do cliente ao pedido
- **Gestão de Mesas**: Controle simples de localização na cafeteria
- **Registro de Pedido**: Interface intuitiva para adicionar itens
- **Customização**: Opções de personalização por produto
- **Divisão por Área de Preparo**: Separação entre cafés, alimentos, etc.
- **Status de Preparo**: Acompanhamento do pedido em tempo real
- **Fechamento de Conta**: Cálculo de total, desconto e pontos gerados

### 3. Programa de Fidelidade
- **Pontuação Automática**: Acúmulo baseado no valor da compra
- **Níveis de Fidelidade**: Benefícios progressivos por nível
- **Resgate de Pontos**: Aplicação de desconto ou itens grátis
- **Histórico de Transações**: Registro de pontos ganhos e utilizados
- **Regras Flexíveis**: Configuração de parâmetros do programa
- **Notificações**: Alerta de pontuação no fechamento da conta

### 4. Personalização e Experiência
- **Registro de Preferências**: Cafés favoritos, método de preparo, etc.
- **Recomendações**: Sugestões baseadas em histórico
- **Ocasiões Especiais**: Registro e alerta de aniversários
- **Feedback Simplificado**: Avaliação rápida após atendimento

## Interfaces

### 1. Interface de Atendimento (Tablet/Desktop)
- **Dashboard inicial**: Visão de mesas e status de pedidos
- **Busca de clientes**: Campo de busca rápida por nome/telefone
- **Perfil do cliente**: Card com informações essenciais e histórico
- **Comanda digital**: Interface para registro e gestão de pedidos
- **Fechamento**: Tela de pagamento, desconto e fidelidade

### 2. Interface de Cozinha/Barista (Tablet/Desktop)
- **Fila de pedidos**: Organizada por tipo e prioridade
- **Detalhes de preparo**: Especificações e customizações
- **Controle de status**: Botões para atualizar andamento

### 3. App para Cliente (Fase inicial - MVP)
- **Perfil**: Dados pessoais e preferências
- **Carteira digital**: Pontos acumulados e histórico
- **Histórico de pedidos**: Últimas visitas e itens consumidos
- **Feedback**: Avaliação simples de experiências

## Integrações

### 1. Firebase Services
- **Authentication**: Login de funcionários e clientes
- **Firestore**: Banco de dados para todas as coleções
- **Cloud Functions**: Regras de negócio e automações
- **Storage**: Armazenamento de imagens de produtos e perfis

### 2. Integrações Externas (Fase Inicial)
- **WhatsApp Business API**: Notificações básicas para clientes
- **API para emissão de NFC-e**: Integração fiscal simplificada

## Fluxos Principais

### 1. Cadastro de Cliente (Primeiro Atendimento)
```
1. Atendente pergunta se é primeira visita
2. Em caso positivo, solicita nome e telefone
3. Sistema cria cadastro básico
4. Sistema atribui tag "novo cliente"
5. Atendente registra preferências iniciais (opcional)
6. Sistema exibe tela de novo pedido associado ao cliente
```

### 2. Atendimento de Cliente Recorrente
```
1. Atendente busca cliente por nome ou telefone
2. Sistema exibe perfil, histórico e preferências
3. Atendente confirma identidade
4. Sistema mostra status no programa de fidelidade
5. Atendente registra novo pedido associado ao cliente
6. Sistema sugere itens baseados em histórico (opcional)
```

### 3. Processamento de Pedido
```
1. Atendente registra itens do pedido
2. Sistema separa itens por área de preparo
3. Baristas/cozinheiros recebem notificação
4. Cada item tem status atualizado durante preparo
5. Atendente é notificado quando itens estão prontos
6. Pedido é entregue ao cliente
```

### 4. Fechamento de Conta e Fidelidade
```
1. Atendente acessa pedido ativo do cliente
2. Sistema exibe resumo dos itens e valor total
3. Atendente seleciona método de pagamento
4. Sistema calcula pontos gerados automaticamente
5. Cliente pode optar por resgatar pontos (desconto)
6. Sistema atualiza saldo de pontos e nível de fidelidade
7. Cliente recebe notificação via WhatsApp (opcional)
```

## Relatórios Iniciais

1. **Dashboard Diário**
   - Total de clientes atendidos
   - Ticket médio
   - Produtos mais vendidos
   - Novos clientes cadastrados

2. **Relatório de Clientes**
   - Clientes mais frequentes
   - Clientes inativos (sem visita há mais de 30 dias)
   - Distribuição por nível de fidelidade
   - Aniversariantes do mês

3. **Relatório de Vendas**
   - Volume por categoria de produto
   - Desempenho por período do dia
   - Métricas de fidelidade (pontos gerados e resgatados)
   - Formas de pagamento

## Implementação Técnica

### Stack Tecnológico
- **Frontend**: Flutter (cross-platform)
- **Backend**: Firebase (Firestore, Auth, Functions)
- **Arquitetura**: Clean Architecture / MVVM

### Estratégia de Desenvolvimento
1. **Semana 1-2**: Modelagem de dados e estrutura básica
2. **Semana 3-4**: Interface de atendimento e cadastro de clientes
3. **Semana 5-6**: Sistema de pedidos e integração com áreas de preparo
4. **Semana 7-8**: Programa de fidelidade e fechamento de conta
5. **Semana 9-10**: Relatórios, testes e ajustes finais

### Considerações de Segurança
- Regras de Firestore para controle de acesso
- Autenticação de dois fatores para administradores
- Backup automático diário dos dados
- Logs de auditoria para operações sensíveis

## Expansão Futura

Este módulo inicial servirá como base para:

1. **App completo para clientes** (pedidos, delivery, reservas)
2. **Módulo B2B** (integração com o cadastro de clientes atual)
3. **Sistema de estoque avançado** (baixa automática de insumos)
4. **Marketing automatizado** (comunicações baseadas em comportamento)
5. **Business Intelligence** (análises avançadas de padrões de consumo)

## Métricas de Sucesso

Para avaliar o sucesso do módulo inicial, serão monitorados:

1. **Tempo de cadastro**: Redução no tempo de registro de novos clientes
2. **Taxa de identificação**: % de pedidos associados a clientes cadastrados
3. **Engajamento de fidelidade**: % de clientes que retornam após primeira visita
4. **Eficiência operacional**: Tempo médio de atendimento e preparo
5. **NPS**: Índice de satisfação dos clientes com o novo processo

---

## Próximos Passos para Implementação

1. Validação do modelo de dados com equipe técnica
2. Configuração do ambiente Firebase
3. Desenvolvimento dos protótipos de interface
4. Implementação das regras de negócio em Cloud Functions
5. Teste piloto com grupo controlado de clientes
6. Treinamento da equipe de atendimento
7. Lançamento e monitoramento inicial
