import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/products/data/providers/product_category_provider.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/presentation/controllers/product_category_notifier.dart';

/// Controller de conveniência para manter compatibilidade com código existente
/// Este controller agora é apenas um wrapper que delega para o StateNotifier
class ProductCategoryController {
  final Ref ref;
  
  ProductCategoryController(this.ref);
  
  /// Obtém o notifier para operações
  ProductCategoryNotifier get _notifier => ref.read(productCategoryNotifierProvider.notifier);
  
  /// Obtém todas as categorias
  Future<List<ProductCategory>> getAllCategories() async {
    await _notifier.loadAllCategories();
    return ref.read(productCategoryNotifierProvider).categories;
  }
  
  /// Obtém categorias por tipo
  Future<List<ProductCategory>> getCategoriesByType(ProductType type) async {
    await _notifier.loadCategoriesByType(type);
    return ref.read(productCategoryNotifierProvider).getCategoriesByType(type);
  }
  
  /// Obtém uma categoria pelo ID
  Future<ProductCategory?> getCategoryById(String id) async {
    await _notifier.loadCategoryById(id);
    return ref.read(productCategoryNotifierProvider).getCategoryById(id);
  }
  
  /// Adiciona uma nova categoria
  Future<String?> addCategory(ProductCategory category) async {
    return await _notifier.addCategory(category);
  }
  
  /// Atualiza uma categoria existente
  Future<bool> updateCategory(ProductCategory category) async {
    return await _notifier.updateCategory(category);
  }
  
  /// Exclui uma categoria
  Future<bool> deleteCategory(String id) async {
    return await _notifier.deleteCategory(id);
  }
  
  /// Atualiza a ordem das categorias
  Future<bool> updateCategoriesOrder(List<String> categoryIds) async {
    return await _notifier.updateCategoriesOrder(categoryIds);
  }
  
  /// Ativa/desativa uma categoria
  Future<bool> toggleCategoryActive(String id, bool isActive) async {
    return await _notifier.toggleCategoryActive(id, isActive);
  }
  
  /// Adiciona um campo personalizado à categoria atual
  void addCustomFieldToCurrentCategory(CustomField field) {
    _notifier.addCustomFieldToCurrentCategory(field);
  }
  
  /// Remove um campo personalizado da categoria atual
  void removeCustomFieldFromCurrentCategory(String fieldId) {
    _notifier.removeCustomFieldFromCurrentCategory(fieldId);
  }
  
  /// Atualiza um campo personalizado na categoria atual
  void updateCustomFieldInCurrentCategory(CustomField updatedField) {
    _notifier.updateCustomFieldInCurrentCategory(updatedField);
  }
  
  /// Define a categoria atual
  void setCurrentCategory(ProductCategory? category) {
    _notifier.setCurrentCategory(category);
  }
  
  /// Limpa mensagens de erro e sucesso
  void clearMessages() {
    _notifier.clearMessages();
  }
  
  /// Redefine o estado para o inicial
  void reset() {
    _notifier.reset();
  }
}

final productCategoryControllerProvider = Provider<ProductCategoryController>((ref) {
  return ProductCategoryController(ref);
}); 