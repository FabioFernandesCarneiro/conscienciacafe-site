# CLAUDE.md

Este arquivo orienta o Claude Code ao trabalhar no app Café.

## Visão Geral

App PWA para frente de loja do Consciência Café. Interface para baristas registrarem pedidos com foco no cliente (customer-first).

**Stack:** Next.js 14 | Firebase Realtime Database | Tailwind CSS | Zustand | Headless UI

## ⚠️ CRÍTICO: Firebase Hosting é Estático

### Configuração
O app usa `output: 'export'` no next.config.js para gerar build estático compatível com Firebase Hosting.

### ✅ O que FUNCIONA:
- Client Components (`'use client'`)
- Firebase Auth (client-side)
- Firebase Realtime Database (client-side)
- Rotas estáticas e dinâmicas pré-renderizadas
- PWA / Service Worker

### ❌ NUNCA usar:
- API Routes (`app/api/*`)
- Server Components dinâmicos
- `getServerSideProps`
- Middleware com lógica de servidor
- Image Optimization (usar `unoptimized: true`)
- Server Actions

### Se precisar de backend:
Usar Firebase Cloud Functions como backend separado.

## Arquitetura

```
app/
├── (auth)/             # Login e autenticação
├── (barista)/          # Interface do barista
├── (caixa)/            # Fechamento de caixa
└── (admin)/            # Dashboard administrativo

components/             # Componentes React
lib/
├── firebase/           # Configuração e helpers Firebase
├── hooks/              # Custom hooks
├── contexts/           # React contexts (Auth, etc)
└── types/              # TypeScript types
```

## Comandos

```bash
npm run dev             # Desenvolvimento (porta 3001)
npm run build           # Build de produção (gera pasta out/)
npm run lint            # Lint
```

## Padrões

### Componentes
- **'use client'** no topo de componentes interativos
- Tailwind para estilização
- Heroicons para ícones
- Headless UI para modais/transições

### Estado
- Zustand para estado global
- Firebase Realtime para dados sincronizados
- React state para UI local

### Cores do tema (Brandbook)
- Primary: `#000000` (preto)
- Accent: `#FF4611` (laranja)
- Accent Hover: `#E53E0F`
- Gray Light: `#F5F5F5`
- Gray Mid: `#6B7280`
- Gray Dark: `#374151`
- Proporção: 60% branco, 30% preto, 10% laranja

### Tipografia
- Títulos: Playfair Display (700)
- Corpo: Inter (400, 500, 600)

### Mobile-First
- Touch-friendly: botões mínimo 44x44px
- Thumb zone: ações principais na parte inferior
- Navegação inferior: BottomNav fixo
- Fontes legíveis: mínimo 16px texto, 14px labels

## Perfis de Usuário

- **Gestor**: Acesso total (admin, funcionários, produtos)
- **Gerente**: Pedidos, caixa, clientes
- **Barista**: Apenas pedidos ativos

## Fluxo Principal

1. Login com email/senha ou Google
2. Barista busca cliente por nome/telefone
3. Sistema mostra: último pedido, cashback, preferências
4. Barista registra pedido vinculado ao cliente
5. Pedido imprime dividido (bebidas/comidas)
6. Fechamento de conta com crédito de pontos

## Firebase Collections

- `users/{uid}` - Usuários/funcionários
- `customers/{id}` - Clientes
- `orders/{id}` - Pedidos
- `products/{id}` - Produtos
- `cashRegisters/{id}` - Caixas
