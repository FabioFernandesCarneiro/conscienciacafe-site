import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/shared/widgets/module_header.dart';

/// Enumeração para identificar a aba ativa
enum ProductModuleTab {
  products,     // Produtos
  categories,   // Categorias
  customizations  // Personalizações
}

/// Provider para controlar a aba atual
final currentProductTabProvider = StateProvider<ProductModuleTab>((ref) {
  return ProductModuleTab.products;
});

class ProductsModuleScreen extends ConsumerStatefulWidget {
  final Widget child;
  
  const ProductsModuleScreen({
    super.key,
    required this.child,
  });

  @override
  ConsumerState<ProductsModuleScreen> createState() => _ProductsModuleScreenState();
}

class _ProductsModuleScreenState extends ConsumerState<ProductsModuleScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: ProductModuleTab.values.length, 
      vsync: this,
      initialIndex: ref.read(currentProductTabProvider).index,
    );
    
    // Adiciona listener para atualizar o provider quando a aba mudar
    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        ref.read(currentProductTabProvider.notifier).state = 
            ProductModuleTab.values[_tabController.index];
      }
    });
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Monitora mudanças na aba atual via provider
    final currentTab = ref.watch(currentProductTabProvider);
    
    // Sincroniza o controlador de abas com o provider
    if (_tabController.index != currentTab.index) {
      _tabController.animateTo(currentTab.index);
    }
    
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: ModuleHeader(
        title: 'Produtos',
        moduleColor: const Color(0xFF4CAF50),
        moduleIcon: Icons.inventory_2_outlined,
        showBackButton: true,
        backRoute: AppConstants.routeAdminModule,
      ),
      body: Column(
        children: [
          // Abas de navegação
          Container(
            color: Colors.white,
            child: TabBar(
              controller: _tabController,
              labelColor: const Color(0xFF4CAF50),
              unselectedLabelColor: Colors.grey,
              indicatorColor: const Color(0xFF4CAF50),
              tabs: [
                Tab(
                  text: 'Produtos',
                  icon: Icon(
                    Icons.inventory_2_outlined,
                    size: 20.sp,
                  ),
                ),
                Tab(
                  text: 'Categorias',
                  icon: Icon(
                    Icons.category_outlined,
                    size: 20.sp,
                  ),
                ),
                Tab(
                  text: 'Personaliz.',
                  icon: Icon(
                    Icons.tune_outlined,
                    size: 20.sp,
                  ),
                ),
              ],
              onTap: (index) {
                // Navega para a rota apropriada com base na aba selecionada
                _navigateToTab(context, ProductModuleTab.values[index]);
              },
            ),
          ),
          
          // Conteúdo da aba atual (vem via child)
          Expanded(
            child: widget.child,
          ),
        ],
      ),
    );
  }
  
  /// Navega para a rota apropriada com base na aba selecionada
  void _navigateToTab(BuildContext context, ProductModuleTab tab) {
    switch (tab) {
      case ProductModuleTab.products:
        context.go('/admin/products');
        break;
      case ProductModuleTab.categories:
        context.go('/admin/products/categories');
        break;
      case ProductModuleTab.customizations:
        context.go('/admin/products/customizations');
        break;
    }
  }
} 