import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/core/errors/error_handler.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/domain/usecases/get_product_categories_usecase.dart';
import 'package:intellicoffee/features/products/domain/usecases/manage_product_category_usecase.dart';
import 'package:intellicoffee/features/products/presentation/controllers/product_category_state.dart';

/// StateNotifier para gerenciamento de categorias de produto
class ProductCategoryNotifier extends StateNotifier<ProductCategoryState> {
  final GetProductCategoriesUseCase _getUseCase;
  final ManageProductCategoryUseCase _manageUseCase;

  ProductCategoryNotifier(this._getUseCase, this._manageUseCase) : super(ProductCategoryState.initial());

  /// Carrega todas as categorias
  Future<void> loadAllCategories() async {
    if (state.isLoading) return;

    state = state.loading();

    try {
      final categories = await _getUseCase.call();
      state = state.success(categories: categories);
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
    }
  }

  /// Carrega categorias por tipo
  Future<void> loadCategoriesByType(ProductType type) async {
    if (state.isLoading) return;

    state = state.loading();

    try {
      final categories = await _getUseCase.getCategoriesByType(type);
      state = state.success(categories: categories);
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
    }
  }

  /// Carrega uma categoria específica por ID
  Future<void> loadCategoryById(String id) async {
    if (state.isLoading) return;

    state = state.loading();

    try {
      // Carrega todas as categorias se não estão carregadas
      if (state.categories.isEmpty) {
        final categories = await _getUseCase.call();
        state = state.success(categories: categories);
      }
      
      final category = state.getCategoryById(id);
      if (category != null) {
        state = state.copyWith(currentCategory: category, isLoading: false);
      } else {
        state = state.failure('Categoria não encontrada');
      }
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
    }
  }

  /// Define a categoria atual
  void setCurrentCategory(ProductCategory? category) {
    state = state.copyWith(currentCategory: category);
  }

  /// Adiciona uma nova categoria
  Future<String?> addCategory(ProductCategory category) async {
    if (state.isLoading) return null;

    state = state.loading();

    try {
      final categoryId = await _manageUseCase.createCategory(category);
      
      // Adiciona a categoria à lista local
      final updatedCategories = [...state.categories, category.copyWith(id: categoryId)];
      
      state = state.success(
        categories: updatedCategories,
        message: 'Categoria adicionada com sucesso',
      );
      
      return categoryId;
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
      return null;
    }
  }

  /// Atualiza uma categoria existente
  Future<bool> updateCategory(ProductCategory category) async {
    if (state.isLoading) return false;

    state = state.loading();

    try {
      await _manageUseCase.updateCategory(category);
      
      // Atualiza a categoria na lista local
      final updatedCategories = state.categories.map((c) {
        return c.id == category.id ? category : c;
      }).toList();
      
      // Atualiza a categoria atual se for a mesma
      ProductCategory? updatedCurrentCategory = state.currentCategory;
      if (state.currentCategory?.id == category.id) {
        updatedCurrentCategory = category;
      }
      
      state = state.success(
        categories: updatedCategories,
        currentCategory: updatedCurrentCategory,
        message: 'Categoria atualizada com sucesso',
      );
      
      return true;
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
      return false;
    }
  }

  /// Exclui uma categoria
  Future<bool> deleteCategory(String id) async {
    if (state.isLoading) return false;

    state = state.loading();

    try {
      await _manageUseCase.deleteCategory(id);
      
      // Remove a categoria da lista local
      final updatedCategories = state.categories
          .where((category) => category.id != id)
          .toList();
      
      // Limpa a categoria atual se for a que foi excluída
      ProductCategory? updatedCurrentCategory = state.currentCategory;
      if (state.currentCategory?.id == id) {
        updatedCurrentCategory = null;
      }
      
      state = state.success(
        categories: updatedCategories,
        currentCategory: updatedCurrentCategory,
        message: 'Categoria excluída com sucesso',
      );
      
      return true;
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
      return false;
    }
  }

  /// Atualiza a ordem das categorias
  Future<bool> updateCategoriesOrder(List<String> categoryIds) async {
    if (state.isLoading) return false;

    state = state.loading();

    try {
      await _manageUseCase.reorderCategories(categoryIds);
      
      // Reordena a lista local baseada na nova ordem
      final reorderedCategories = <ProductCategory>[];
      for (final id in categoryIds) {
        final category = state.categories.firstWhere((c) => c.id == id);
        reorderedCategories.add(category.copyWith(order: categoryIds.indexOf(id)));
      }
      
      state = state.success(
        categories: reorderedCategories,
        message: 'Ordem das categorias atualizada',
      );
      
      return true;
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
      return false;
    }
  }

  /// Ativa/desativa uma categoria
  Future<bool> toggleCategoryActive(String id, bool isActive) async {
    if (state.isLoading) return false;

    state = state.loading();

    try {
      await _manageUseCase.toggleCategoryStatus(id, isActive);
      
      // Atualiza o status na lista local
      final updatedCategories = state.categories.map((category) {
        if (category.id == id) {
          return category.copyWith(isActive: isActive);
        }
        return category;
      }).toList();
      
      // Atualiza a categoria atual se for a mesma
      ProductCategory? updatedCurrentCategory = state.currentCategory;
      if (state.currentCategory?.id == id) {
        updatedCurrentCategory = state.currentCategory!.copyWith(isActive: isActive);
      }
      
      state = state.success(
        categories: updatedCategories,
        currentCategory: updatedCurrentCategory,
        message: isActive ? 'Categoria ativada' : 'Categoria desativada',
      );
      
      return true;
    } catch (e, stackTrace) {
      final appError = AppErrorHandler.handleError(e, stackTrace);
      state = state.failure(appError.message);
      return false;
    }
  }

  /// Adiciona um campo personalizado à categoria atual
  void addCustomFieldToCurrentCategory(CustomField field) {
    final currentCategory = state.currentCategory;
    if (currentCategory == null) return;
    
    final updatedFields = [...currentCategory.customFields, field];
    final updatedCategory = currentCategory.copyWith(customFields: updatedFields);
    
    state = state.copyWith(currentCategory: updatedCategory);
  }

  /// Remove um campo personalizado da categoria atual
  void removeCustomFieldFromCurrentCategory(String fieldId) {
    final currentCategory = state.currentCategory;
    if (currentCategory == null) return;
    
    final updatedFields = currentCategory.customFields
        .where((field) => field.id != fieldId)
        .toList();
    
    final updatedCategory = currentCategory.copyWith(customFields: updatedFields);
    state = state.copyWith(currentCategory: updatedCategory);
  }

  /// Atualiza um campo personalizado na categoria atual
  void updateCustomFieldInCurrentCategory(CustomField updatedField) {
    final currentCategory = state.currentCategory;
    if (currentCategory == null) return;
    
    final updatedFields = currentCategory.customFields.map((field) {
      return field.id == updatedField.id ? updatedField : field;
    }).toList();
    
    final updatedCategory = currentCategory.copyWith(customFields: updatedFields);
    state = state.copyWith(currentCategory: updatedCategory);
  }

  /// Limpa mensagens de erro e sucesso
  void clearMessages() {
    state = state.copyWith(error: null, successMessage: null);
  }

  /// Redefine o estado para o inicial
  void reset() {
    state = ProductCategoryState.initial();
  }
}