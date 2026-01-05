import 'package:intellicoffee/features/products/domain/models/product_category.dart';

/// Estado para gerenciamento de categorias de produto
class ProductCategoryState {
  final List<ProductCategory> categories;
  final ProductCategory? currentCategory;
  final bool isLoading;
  final String? error;
  final String? successMessage;

  const ProductCategoryState({
    this.categories = const [],
    this.currentCategory,
    this.isLoading = false,
    this.error,
    this.successMessage,
  });

  /// Estado inicial
  factory ProductCategoryState.initial() {
    return const ProductCategoryState();
  }

  /// Estado de carregamento
  ProductCategoryState loading() {
    return copyWith(
      isLoading: true,
      error: null,
      successMessage: null,
    );
  }

  /// Estado de sucesso
  ProductCategoryState success({
    List<ProductCategory>? categories,
    ProductCategory? currentCategory,
    String? message,
  }) {
    return copyWith(
      categories: categories ?? this.categories,
      currentCategory: currentCategory ?? this.currentCategory,
      isLoading: false,
      error: null,
      successMessage: message,
    );
  }

  /// Estado de erro
  ProductCategoryState failure(String error) {
    return copyWith(
      isLoading: false,
      error: error,
      successMessage: null,
    );
  }

  /// Copia o estado com novos valores
  ProductCategoryState copyWith({
    List<ProductCategory>? categories,
    ProductCategory? currentCategory,
    bool? isLoading,
    String? error,
    String? successMessage,
  }) {
    return ProductCategoryState(
      categories: categories ?? this.categories,
      currentCategory: currentCategory ?? this.currentCategory,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      successMessage: successMessage,
    );
  }

  /// Verifica se há erro
  bool get hasError => error != null;

  /// Verifica se há mensagem de sucesso
  bool get hasSuccess => successMessage != null;

  /// Obtém categoria por ID
  ProductCategory? getCategoryById(String id) {
    try {
      return categories.firstWhere((category) => category.id == id);
    } catch (e) {
      return null;
    }
  }

  /// Obtém categorias por tipo
  List<ProductCategory> getCategoriesByType(ProductType type) {
    return categories.where((category) => category.productType == type).toList();
  }

  /// Obtém categorias ativas
  List<ProductCategory> get activeCategories {
    return categories.where((category) => category.isActive).toList();
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is ProductCategoryState &&
        other.categories == categories &&
        other.currentCategory == currentCategory &&
        other.isLoading == isLoading &&
        other.error == error &&
        other.successMessage == successMessage;
  }

  @override
  int get hashCode {
    return categories.hashCode ^
        currentCategory.hashCode ^
        isLoading.hashCode ^
        error.hashCode ^
        successMessage.hashCode;
  }

  @override
  String toString() {
    return 'ProductCategoryState(categories: ${categories.length}, currentCategory: ${currentCategory?.name}, isLoading: $isLoading, error: $error, successMessage: $successMessage)';
  }
}