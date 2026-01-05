import '../models/product_category.dart';

/// Interface para o repositório de categorias de produto
abstract class ProductCategoryRepository {
  /// Obtém todas as categorias de produto
  Future<List<ProductCategory>> getAllCategories();
  
  /// Obtém categorias de produto por tipo
  Future<List<ProductCategory>> getCategoriesByType(ProductType type);
  
  /// Obtém uma categoria de produto pelo ID
  Future<ProductCategory?> getCategoryById(String id);
  
  /// Adiciona uma nova categoria de produto
  Future<String> addCategory(ProductCategory category);
  
  /// Atualiza uma categoria de produto existente
  Future<void> updateCategory(ProductCategory category);
  
  /// Exclui uma categoria de produto
  Future<void> deleteCategory(String id);
  
  /// Atualiza a ordem das categorias
  Future<void> updateCategoriesOrder(List<String> categoryIds);
  
  /// Ativa ou desativa uma categoria
  Future<void> toggleCategoryActive(String id, bool isActive);
} 