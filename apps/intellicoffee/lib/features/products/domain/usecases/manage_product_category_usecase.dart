import 'package:intellicoffee/core/errors/app_error.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/domain/repositories/product_category_repository.dart';

/// Use case para gerenciar categorias de produtos (CRUD)
class ManageProductCategoryUseCase {
  final ProductCategoryRepository _repository;

  ManageProductCategoryUseCase(this._repository);

  /// Cria uma nova categoria
  Future<String> createCategory(ProductCategory category) async {
    // Validações de negócio
    await _validateCategoryName(category.name, excludeId: category.id);
    _validateCategoryData(category);

    // Definir ordem automaticamente se não foi especificada
    if (category.order == 0) {
      final categories = await _repository.getCategoriesByType(category.productType);
      final maxOrder = categories.isEmpty 
          ? 0 
          : categories.map((c) => c.order).reduce((a, b) => a > b ? a : b);
      
      category = category.copyWith(order: maxOrder + 1);
    }

    return await _repository.addCategory(category);
  }

  /// Atualiza uma categoria existente
  Future<void> updateCategory(ProductCategory category) async {
    // Validações de negócio
    await _validateCategoryExists(category.id);
    await _validateCategoryName(category.name, excludeId: category.id);
    _validateCategoryData(category);

    await _repository.updateCategory(category);
  }

  /// Exclui uma categoria
  Future<void> deleteCategory(String categoryId) async {
    // Validações de negócio
    await _validateCategoryExists(categoryId);
    await _validateCategoryCanBeDeleted(categoryId);

    await _repository.deleteCategory(categoryId);
  }

  /// Ativa/desativa uma categoria
  Future<void> toggleCategoryStatus(String categoryId, bool isActive) async {
    await _validateCategoryExists(categoryId);
    await _repository.toggleCategoryActive(categoryId, isActive);
  }

  /// Reordena categorias
  Future<void> reorderCategories(List<String> categoryIds) async {
    // Validar se todas as categorias existem
    for (final id in categoryIds) {
      await _validateCategoryExists(id);
    }

    await _repository.updateCategoriesOrder(categoryIds);
  }

  /// Duplica uma categoria
  Future<String> duplicateCategory(String categoryId) async {
    final originalCategory = await _repository.getCategoryById(categoryId);
    if (originalCategory == null) {
      throw DataError.notFound('Categoria');
    }

    // Criar cópia com novo nome
    final duplicatedCategory = originalCategory.copyWith(
      id: '', // Será gerado um novo ID
      name: '${originalCategory.name} (Cópia)',
      order: originalCategory.order + 1,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    return await createCategory(duplicatedCategory);
  }

  /// Importa categorias em lote
  Future<BatchImportResult> importCategories(List<ProductCategory> categories) async {
    final results = BatchImportResult();

    for (final category in categories) {
      try {
        await _validateCategoryName(category.name);
        _validateCategoryData(category);
        
        final categoryId = await _repository.addCategory(category);
        results.addSuccess(categoryId, category.name);
      } catch (e) {
        results.addError(category.name, e.toString());
      }
    }

    return results;
  }

  /// Validações privadas

  Future<void> _validateCategoryExists(String categoryId) async {
    final category = await _repository.getCategoryById(categoryId);
    if (category == null) {
      throw DataError.notFound('Categoria');
    }
  }

  Future<void> _validateCategoryName(String name, {String? excludeId}) async {
    if (name.trim().isEmpty) {
      throw ValidationError.required('Nome da categoria');
    }

    if (name.trim().length < 2) {
      throw ValidationError.invalid('Nome da categoria', 'Deve ter pelo menos 2 caracteres');
    }

    // Verificar duplicidade
    final existingCategories = await _repository.getAllCategories();
    final duplicateCategory = existingCategories.where((category) {
      return category.name.toLowerCase() == name.toLowerCase() &&
             category.id != excludeId;
    }).firstOrNull;

    if (duplicateCategory != null) {
      throw DataError.alreadyExists('Categoria com este nome');
    }
  }

  void _validateCategoryData(ProductCategory category) {
    // Validar campos personalizados
    for (final field in category.customFields) {
      if (field.name.trim().isEmpty) {
        throw ValidationError.required('Nome do campo personalizado');
      }
    }

    // Validar descrição
    if (category.description.length > 500) {
      throw ValidationError.invalid('Descrição', 'Não pode ter mais de 500 caracteres');
    }
  }

  Future<void> _validateCategoryCanBeDeleted(String categoryId) async {
    // Aqui você pode implementar validações específicas
    // Por exemplo, verificar se a categoria não está sendo usada por produtos
    
    // TODO: Implementar verificação de produtos associados
    // final products = await _productRepository.getProductsByCategoryId(categoryId);
    // if (products.isNotEmpty) {
    //   throw ValidationError(
    //     message: 'Categoria não pode ser excluída pois possui produtos associados',
    //     code: 'CATEGORY_HAS_PRODUCTS',
    //   );
    // }
  }
}

/// Resultado de importação em lote
class BatchImportResult {
  final List<BatchImportSuccess> successes = [];
  final List<BatchImportError> errors = [];

  void addSuccess(String id, String name) {
    successes.add(BatchImportSuccess(id: id, name: name));
  }

  void addError(String name, String error) {
    errors.add(BatchImportError(name: name, error: error));
  }

  bool get hasErrors => errors.isNotEmpty;
  bool get hasSuccesses => successes.isNotEmpty;
  int get totalProcessed => successes.length + errors.length;
  double get successRate => totalProcessed > 0 ? (successes.length / totalProcessed) * 100 : 0;
}

class BatchImportSuccess {
  final String id;
  final String name;

  BatchImportSuccess({required this.id, required this.name});
}

class BatchImportError {
  final String name;
  final String error;

  BatchImportError({required this.name, required this.error});
}