// Customer types
export interface Customer {
  id: string;
  name: string;
  phone: string;
  type: 'b2c' | 'b2b';
  companyName?: string;
  createdAt: Date;
  lastVisit: Date;
  totalVisits: number;
  totalSpent: number;
  preferences: CustomerPreferences;
  loyalty: LoyaltyInfo;
}

export interface CustomerPreferences {
  favoriteOrder?: string;
  sensoryProfile?: SensoryProfile;
  notes?: string;
}

export interface SensoryProfile {
  acidity?: 'baixa' | 'media' | 'alta';
  body?: 'leve' | 'medio' | 'encorpado';
  sweetness?: 'baixa' | 'media' | 'alta';
  preferredOrigins?: string[];
}

export type LoyaltyTier = 'iniciante' | 'frequente' | 'habitue' | 'da_casa';

export interface LoyaltyInfo {
  cashback: number;              // Saldo de cashback em R$
  tier: LoyaltyTier;
  visitsThisMonth: number;       // Visitas no mês atual
  lastTierUpdate: Date;          // Última atualização de tier
  history: LoyaltyTransaction[];
}

export interface LoyaltyTransaction {
  id: string;
  date: Date;
  type: 'earn' | 'redeem';       // Ganhou ou usou cashback
  amount: number;                // Valor em R$
  reason: string;
  orderId?: string;
  orderTotal?: number;           // Total do pedido (para earn)
}

// Configuração de cashback por tier
export const CASHBACK_RATES: Record<LoyaltyTier, number> = {
  iniciante: 0.05,    // 5%
  frequente: 0.07,    // 7% (4+ visitas/mês)
  habitue: 0.10,      // 10% (8+ visitas/mês)
  da_casa: 0.10,      // 10% (12+ visitas/mês) + experiências exclusivas
};

export const TIER_THRESHOLDS: Record<LoyaltyTier, number> = {
  iniciante: 0,
  frequente: 4,       // 4+ visitas/mês
  habitue: 8,         // 8+ visitas/mês
  da_casa: 12,        // 12+ visitas/mês
};

// Order types
export type OrderStatus = 'open' | 'preparing' | 'ready' | 'paid' | 'cancelled';
export type Station = 'bebidas' | 'comidas';

export interface OrderItem {
  id: string;
  productId: string;
  name: string;
  price: number;
  quantity: number;
  station: Station;
  notes?: string;
  addedBy: string;
  addedAt: Date;
}

export interface Payment {
  method: PaymentMethod;
  amount: number;
  paidAt: Date;
}

export type PaymentMethod =
  | 'cash'
  | 'credit'
  | 'debit'
  | 'pix'
  | 'giftcard'
  | 'marketplace';

export interface Order {
  id: string;
  customerId?: string;
  customerName: string;
  status: OrderStatus;
  items: OrderItem[];
  payments: Payment[];
  baristaId: string;
  baristaName: string;
  createdAt: Date;
  paidAt?: Date;
  total: number;
  discount?: number;
  cashbackEarned?: number;        // Cashback ganho neste pedido
  cashbackUsed?: number;          // Cashback usado como pagamento
}

// Product types
export type ProductType =
  | 'produto'
  | 'servico';

export type PriceChannel = 'balcao' | 'b2b' | 'delivery';

export interface Product {
  id: string;
  name: string;
  description?: string;
  category: string;
  type: ProductType;
  unit: string;
  station: Station;
  stockSection?: string;
  prices: Record<PriceChannel, number>;
  productionCost?: number;
  prepTime?: number;
  divisible: boolean;
  autoWeight: boolean;
  isIngredient: boolean;
  chargeCommission: boolean;
  printAsTicket: boolean;
  stock?: number;
  minStock?: number;
  maxStock?: number;
  images: string[];
  code?: string;
  abbreviation?: string;
  active: boolean;
}

// Cash Register types
export type CashRegisterStatus = 'open' | 'closed';

export interface CashOperation {
  id: string;
  type: 'insert' | 'withdraw' | 'sangria';
  amount: number;
  reason: string;
  classification?: string;
  destination?: string;
  isExpense: boolean;
  isRevenue: boolean;
  createdAt: Date;
  createdBy: string;
}

export interface PaymentBalance {
  expected: number;
  counted: number;
  difference: number;
}

export interface CashRegisterStats {
  totalOrders: number;
  canceledOrders: number;
  canceledItems: number;
  averageTicket: number;
  averageTime: number;
  averageProducts: number;
}

export interface CashRegisterSales {
  comanda: number;
  products: number;
  commission: number;
  services: number;
  discounts: number;
  total: number;
}

export interface CashRegister {
  id: string;
  number: number;
  movementId: string;
  status: CashRegisterStatus;
  openedBy: string;
  openedAt: Date;
  closedBy?: string;
  closedAt?: Date;
  sales: CashRegisterSales;
  payments: Record<PaymentMethod, PaymentBalance>;
  operations: CashOperation[];
  stats: CashRegisterStats;
  notes?: string;
}

// User types
export type UserRole = 'gestor' | 'gerente' | 'barista';

export interface User {
  id: string;           // Firebase Auth UID
  email: string;
  name: string;
  role: UserRole;
  active: boolean;
  createdAt: string;    // ISO string
  createdBy: string;    // UID of creator
  lastLogin?: string;   // ISO string
  photoURL?: string;
}

// Role permissions helper
export const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  gestor: ['admin', 'funcionarios', 'produtos', 'caixa', 'pedidos', 'clientes'],
  gerente: ['caixa', 'pedidos', 'clientes'],
  barista: ['pedidos'],
};

// Alias for backwards compatibility
export type Barista = User;
