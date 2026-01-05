import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/products/data/providers/product_category_provider.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/domain/usecases/get_product_categories_usecase.dart';
import 'package:intellicoffee/features/products/domain/usecases/manage_product_category_usecase.dart';

/// Provider para o use case de obter categorias
final getProductCategoriesUseCaseProvider = Provider<GetProductCategoriesUseCase>((ref) {
  final repository = ref.watch(productCategoryRepositoryProvider);
  return GetProductCategoriesUseCase(repository);
});

/// Provider para o use case de gerenciar categorias
final manageProductCategoryUseCaseProvider = Provider<ManageProductCategoryUseCase>((ref) {
  final repository = ref.watch(productCategoryRepositoryProvider);
  return ManageProductCategoryUseCase(repository);
});

/// Provider para estatísticas de categorias
final categoryStatisticsProvider = FutureProvider<CategoryStatistics>((ref) async {
  final useCase = ref.watch(getProductCategoriesUseCaseProvider);
  return useCase.getCategoryStatistics();
});

/// Provider para categorias ativas apenas
final activeCategoriesProvider = FutureProvider<List<ProductCategory>>((ref) async {
  final useCase = ref.watch(getProductCategoriesUseCaseProvider);
  return useCase.getActiveCategories();
});

/// Provider para categorias ativas por tipo
final activeCategoriesByTypeProvider = FutureProvider.family<List<ProductCategory>, ProductType>((ref, type) async {
  final useCase = ref.watch(getProductCategoriesUseCaseProvider);
  return useCase.getActiveCategoriesByType(type);
});

/// Provider para busca de categorias
final searchCategoriesProvider = FutureProvider.family<List<ProductCategory>, String>((ref, query) async {
  final useCase = ref.watch(getProductCategoriesUseCaseProvider);
  return useCase.searchCategories(query);
});