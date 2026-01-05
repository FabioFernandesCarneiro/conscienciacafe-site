class AppConstants {
  // App info
  static const String appName = 'IntelliCoffee';
  static const String appVersion = '1.0.0';
  
  // Route names
  static const String routeInitial = '/';
  static const String routeLogin = '/login';
  static const String routeHome = '/home';
  static const String routeServiceModule = '/service';
  static const String routeCustomerModule = '/customers';
  static const String routeRoastingModule = '/roasting';
  static const String routeB2BModule = '/b2b';
  static const String routeEventModule = '/events';
  static const String routeAdminModule = '/admin';
  
  // Rotas aninhadas
  static const String routeCustomerList = '/customers/list';
  static const String routeCustomerDetail = '/customers/:id';
  static const String routeCustomerNew = '/customers/new';
  static const String routeOrderList = '/orders';
  static const String routeOrderDetail = '/orders/:id';
  static const String routeOrderNew = '/orders/new';
  static const String routeProductList = '/products';
  static const String routeProductDetail = '/products/:id';
  
  // Rotas do módulo de gestão
  static const String routeUserList = '/admin/users';
  static const String routeUserDetail = '/admin/users/:id';
  static const String routeUserNew = '/admin/users/new';
  
  // Rotas do módulo de produtos
  static const String routeProductsModule = '/admin/products';
  static const String routeProductCategoryList = '/admin/products/categories';
  static const String routeProductCategoryDetail = '/admin/products/categories/:id';
  static const String routeProductCategoryNew = '/admin/products/categories/new';
  static const String routeProductCustomizationList = '/admin/products/customizations';
  static const String routeProductCustomizationDetail = '/admin/products/customizations/:id';
  static const String routeProductCustomizationNew = '/admin/products/customizations/new';
  
  // Firebase collections
  static const String colUsers = 'users';
  static const String colCustomers = 'customers';
  static const String colOrders = 'orders';
  static const String colProducts = 'products';
  static const String colProductCategories = 'productCategories';
  static const String colProductCustomizations = 'productCustomizations';
  static const String colCoffeeProducts = 'coffeeProducts';
  static const String colLoyaltyRules = 'loyaltyRules';
  static const String colLoyaltyTransactions = 'loyaltyTransactions';
  
  // Module colors
  static const String colorAtendimento = '#FF9800'; // Laranja
  static const String colorClientes = '#2196F3'; // Azul
  static const String colorTorrefacao = '#FFC107'; // Âmbar
  static const String colorVendasB2B = '#3F51B5'; // Índigo
  static const String colorEventos = '#9C27B0'; // Roxo
  static const String colorGestao = '#4CAF50'; // Verde
}