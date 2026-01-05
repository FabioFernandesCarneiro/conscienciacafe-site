import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/domain/repositories/product_category_repository.dart';

/// Use case para obter categorias de produtos
class GetProductCategoriesUseCase {
  final ProductCategoryRepository _repository;

  GetProductCategoriesUseCase(this._repository);

  /// Obtém todas as categorias de produtos
  Future<List<ProductCategory>> call() async {
    final categories = await _repository.getAllCategories();
    
    // Aplicar lógica de negócio se necessário
    // Por exemplo, ordenar por ordem definida
    categories.sort((a, b) => a.order.compareTo(b.order));
    
    return categories;
  }

  /// Obtém apenas categorias ativas
  Future<List<ProductCategory>> getActiveCategories() async {
    final categories = await call();
    return categories.where((category) => category.isActive).toList();
  }

  /// Obtém categorias por tipo
  Future<List<ProductCategory>> getCategoriesByType(ProductType type) async {
    final categories = await _repository.getCategoriesByType(type);
    
    // Aplicar ordenação
    categories.sort((a, b) => a.order.compareTo(b.order));
    
    return categories;
  }

  /// Obtém categorias ativas por tipo
  Future<List<ProductCategory>> getActiveCategoriesByType(ProductType type) async {
    final categories = await getCategoriesByType(type);
    return categories.where((category) => category.isActive).toList();
  }

  /// Busca categorias por nome
  Future<List<ProductCategory>> searchCategories(String query) async {
    if (query.trim().isEmpty) {
      return await call();
    }

    final categories = await call();
    final lowerQuery = query.toLowerCase();
    
    return categories.where((category) {
      return category.name.toLowerCase().contains(lowerQuery) ||
             category.description.toLowerCase().contains(lowerQuery);
    }).toList();
  }

  /// Obtém estatísticas das categorias
  Future<CategoryStatistics> getCategoryStatistics() async {
    final categories = await call();
    
    final totalCategories = categories.length;
    final activeCategories = categories.where((c) => c.isActive).length;
    final inactiveCategories = totalCategories - activeCategories;
    
    final typeDistribution = <ProductType, int>{};
    for (final type in ProductType.values) {
      typeDistribution[type] = categories.where((c) => c.productType == type).length;
    }
    
    return CategoryStatistics(
      totalCategories: totalCategories,
      activeCategories: activeCategories,
      inactiveCategories: inactiveCategories,
      typeDistribution: typeDistribution,
    );
  }
}

/// Classe para estatísticas de categorias
class CategoryStatistics {
  final int totalCategories;
  final int activeCategories;
  final int inactiveCategories;
  final Map<ProductType, int> typeDistribution;

  const CategoryStatistics({
    required this.totalCategories,
    required this.activeCategories,
    required this.inactiveCategories,
    required this.typeDistribution,
  });

  /// Porcentagem de categorias ativas
  double get activePercentage {
    if (totalCategories == 0) return 0;
    return (activeCategories / totalCategories) * 100;
  }

  /// Tipo de produto mais popular
  ProductType? get mostPopularType {
    if (typeDistribution.isEmpty) return null;
    
    var maxCount = 0;
    ProductType? mostPopular;
    
    for (final entry in typeDistribution.entries) {
      if (entry.value > maxCount) {
        maxCount = entry.value;
        mostPopular = entry.key;
      }
    }
    
    return mostPopular;
  }
}