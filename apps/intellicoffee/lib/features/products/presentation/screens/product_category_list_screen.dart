import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/products/data/providers/product_category_provider.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/presentation/controllers/product_category_controller.dart';
import 'package:intellicoffee/shared/widgets/empty_state.dart';
import 'package:intellicoffee/shared/widgets/error_state.dart';

/// Provider para armazenar o filtro de tipo selecionado
final selectedTypeFilterProvider = StateProvider<ProductType?>((ref) => null);

/// Provider para armazenar o termo de busca
final searchQueryProvider = StateProvider<String>((ref) => '');

class ProductCategoryListScreen extends ConsumerStatefulWidget {
  const ProductCategoryListScreen({super.key});

  @override
  ConsumerState<ProductCategoryListScreen> createState() => _ProductCategoryListScreenState();
}

class _ProductCategoryListScreenState extends ConsumerState<ProductCategoryListScreen> {
  @override
  void initState() {
    super.initState();
    // Carrega as categorias quando a tela é inicializada
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(productCategoryNotifierProvider.notifier).loadAllCategories();
    });
  }

  @override
  Widget build(BuildContext context) {
    // Monitora o estado do notifier
    final categoryState = ref.watch(productCategoryNotifierProvider);
    final isLoading = categoryState.isLoading;
    final errorMessage = categoryState.error;
    
    // Carrega as categorias na primeira vez
    ref.listen(productCategoryNotifierProvider, (previous, next) {
      if (next.hasError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.error!),
            backgroundColor: Colors.red,
          ),
        );
      }
      if (next.hasSuccess) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.successMessage!),
            backgroundColor: Colors.green,
          ),
        );
      }
    });
    
    // Termo de busca
    final searchQuery = ref.watch(searchQueryProvider);
    
    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Campo de busca
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 16.h),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8.r),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: TextField(
                onChanged: (value) {
                  ref.read(searchQueryProvider.notifier).state = value;
                },
                decoration: InputDecoration(
                  hintText: 'Buscar categoria...',
                  prefixIcon: Icon(Icons.search, color: Colors.grey[400]),
                  suffixIcon: searchQuery.isNotEmpty
                      ? IconButton(
                          icon: Icon(Icons.clear, color: Colors.grey[400]),
                          onPressed: () {
                            ref.read(searchQueryProvider.notifier).state = '';
                          },
                        )
                      : Icon(Icons.search, color: Colors.grey[400]),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(vertical: 12.h),
                ),
              ),
            ),
          ),
          
          // Abas de filtro
          _buildCategoryTabs(context, ref, categoryState.categories),
          
          // Lista de categorias
          Expanded(
            child: isLoading
                ? const Center(child: CircularProgressIndicator())
                : errorMessage != null
                    ? ErrorState(
                        message: 'Erro ao carregar categorias',
                        onRetry: () => ref.read(productCategoryNotifierProvider.notifier).loadAllCategories(),
                      )
                    : _buildCategoriesList(context, ref, categoryState.categories, searchQuery),
          ),
        ],
      ),
      // Botão de adicionar
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF4CAF50),
        onPressed: () {
          ref.read(productCategoryNotifierProvider.notifier).setCurrentCategory(ProductCategory.empty());
          context.go(AppConstants.routeProductCategoryNew);
        },
        child: const Icon(Icons.add),
      ),
    );
  }
  
  /// Constrói a lista de categorias filtrada
  Widget _buildCategoriesList(BuildContext context, WidgetRef ref, List<ProductCategory> categories, String searchQuery) {
    // Filtrar por busca
    final filteredCategories = categories.where((category) {
      if (searchQuery.isEmpty) return true;
      return category.name.toLowerCase().contains(searchQuery.toLowerCase());
    }).toList();
    
    // Filtrar por tipo
    final selectedType = ref.watch(selectedTypeFilterProvider);
    final typeFilteredCategories = selectedType == null
        ? filteredCategories
        : filteredCategories.where((c) => c.productType == selectedType).toList();
    
    if (typeFilteredCategories.isEmpty) {
      return EmptyState(
        icon: Icons.category_outlined,
        title: 'Nenhuma categoria encontrada',
        message: searchQuery.isNotEmpty 
            ? 'Nenhum resultado para "$searchQuery"'
            : 'Adicione uma nova categoria para começar',
        actionLabel: 'Nova Categoria',
        onAction: () {
          ref.read(productCategoryNotifierProvider.notifier).setCurrentCategory(ProductCategory.empty());
          context.go(AppConstants.routeProductCategoryNew);
        },
      );
    }
    
    return ListView.builder(
      padding: EdgeInsets.all(16.r),
      itemCount: typeFilteredCategories.length,
      itemBuilder: (context, index) {
        return _buildCategoryCard(context, ref, typeFilteredCategories[index]);
      },
    );
  }
  
  /// Constrói as abas de filtro por tipo de produto
  Widget _buildCategoryTabs(BuildContext context, WidgetRef ref, List<ProductCategory> categories) {
    // Contadores
    final totalCount = categories.length;
    
    // Contadores por tipo
    final counters = {
      for (var type in ProductType.values)
        type: categories.where((c) => c.productType == type).length
    };
    
    final selectedType = ref.watch(selectedTypeFilterProvider);
    
    return Container(
      color: Colors.white,
      child: Column(
        children: [
          Divider(height: 1, color: Colors.grey[200]),
          Row(
            children: [
              // Tab "Todos"
              Expanded(
                child: _buildTab(
                  context,
                  label: 'Todos',
                  count: totalCount,
                  isSelected: selectedType == null,
                  color: Colors.green,
                  onTap: () {
                    ref.read(selectedTypeFilterProvider.notifier).state = null;
                  },
                ),
              ),
              
              // Tab por tipo
              ...ProductType.values.where((type) => counters[type]! > 0).map((type) => 
                Expanded(
                  child: _buildTab(
                    context,
                    label: type.displayName,
                    count: counters[type] ?? 0,
                    isSelected: selectedType == type,
                    color: Color(type.color),
                    onTap: () {
                      ref.read(selectedTypeFilterProvider.notifier).state = 
                          selectedType == type ? null : type;
                    },
                  ),
                ),
              ),
            ],
          ),
          Divider(height: 1, color: Colors.grey[200]),
        ],
      ),
    );
  }
  
  /// Constrói uma aba de filtro
  Widget _buildTab(
    BuildContext context, {
    required String label,
    required int count,
    required bool isSelected,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 12.h),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: isSelected ? color : Colors.transparent,
              width: 2.0,
            ),
          ),
        ),
        child: Column(
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                color: isSelected ? color : Colors.grey[600],
              ),
            ),
            SizedBox(height: 4.h),
            Container(
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 2.h),
              decoration: BoxDecoration(
                color: isSelected ? color.withValues(alpha: 0.1) : Colors.grey[200],
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Text(
                count.toString(),
                style: TextStyle(
                  fontSize: 12.sp,
                  fontWeight: FontWeight.bold,
                  color: isSelected ? color : Colors.grey[700],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  /// Constrói o card de categoria
  Widget _buildCategoryCard(BuildContext context, WidgetRef ref, ProductCategory category) {
    final Color typeColor = Color(category.productType.color);
    
    return Card(
      margin: EdgeInsets.only(bottom: 12.h),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8.r),
        side: BorderSide(
          color: Colors.grey[300]!,
          width: 1,
        ),
      ),
      child: InkWell(
        onTap: () {
          // Navega para a tela de detalhes da categoria
          context.go('${AppConstants.routeProductCategoryDetail.replaceAll(':id', '')}${category.id}');
        },
        borderRadius: BorderRadius.circular(8.r),
        child: Padding(
          padding: EdgeInsets.all(16.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  // Ícone do tipo
                  Container(
                    width: 40.r,
                    height: 40.r,
                    decoration: BoxDecoration(
                      color: typeColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                    child: Center(
                      child: Icon(
                        _getIconForType(category.productType),
                        color: typeColor,
                        size: 20.r,
                      ),
                    ),
                  ),
                  SizedBox(width: 12.w),
                  
                  // Nome e tipo
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          category.name,
                          style: TextStyle(
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        SizedBox(height: 4.h),
                        Row(
                          children: [
                            Container(
                              padding: EdgeInsets.symmetric(
                                horizontal: 8.w,
                                vertical: 2.h,
                              ),
                              decoration: BoxDecoration(
                                color: typeColor.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(4.r),
                              ),
                              child: Text(
                                category.productType.displayName,
                                style: TextStyle(
                                  fontSize: 12.sp,
                                  color: typeColor,
                                ),
                              ),
                            ),
                            SizedBox(width: 8.w),
                            Text(
                              category.isActive ? 'Ativo' : 'Inativo',
                              style: TextStyle(
                                fontSize: 12.sp,
                                color: category.isActive ? Colors.green : Colors.red,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  
                  // Ações
                  Row(
                    children: [
                      IconButton(
                        icon: Icon(
                          Icons.edit_outlined,
                          color: Colors.grey[600],
                        ),
                        onPressed: () {
                          context.go('${AppConstants.routeProductCategoryDetail.replaceAll(':id', '')}${category.id}');
                        },
                      ),
                      IconButton(
                        icon: Icon(
                          category.isActive ? Icons.toggle_on : Icons.toggle_off,
                          color: category.isActive ? Colors.green : Colors.grey,
                        ),
                        onPressed: () {
                          // Toggle status da categoria
                          final controller = ref.read(productCategoryControllerProvider);
                          controller.toggleCategoryActive(category.id, !category.isActive);
                        },
                      ),
                    ],
                  ),
                ],
              ),
              
              // Campos personalizados
              if (category.customFields.isNotEmpty) ...[
                SizedBox(height: 12.h),
                Divider(height: 1, color: Colors.grey[200]),
                SizedBox(height: 12.h),
                Text(
                  'Campos personalizados:',
                  style: TextStyle(
                    fontSize: 12.sp,
                    color: Colors.grey[600],
                  ),
                ),
                SizedBox(height: 8.h),
                Wrap(
                  spacing: 8.w,
                  runSpacing: 8.h,
                  children: category.customFields.map((field) {
                    return Container(
                      padding: EdgeInsets.symmetric(
                        horizontal: 8.w,
                        vertical: 4.h,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(4.r),
                      ),
                      child: Text(
                        field.name,
                        style: TextStyle(
                          fontSize: 12.sp,
                          color: Colors.grey[700],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
  
  /// Retorna o ícone apropriado para o tipo de produto
  IconData _getIconForType(ProductType type) {
    switch (type) {
      case ProductType.coffee:
        return Icons.coffee;
      case ProductType.beverage:
        return Icons.local_cafe;
      case ProductType.food:
        return Icons.restaurant;
      case ProductType.accessory:
        return Icons.shopping_bag;
      case ProductType.book:
        return Icons.book;
      case ProductType.ingredient:
        return Icons.egg;
    }
  }
} 