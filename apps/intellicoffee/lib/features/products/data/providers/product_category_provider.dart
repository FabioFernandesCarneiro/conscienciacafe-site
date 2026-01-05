import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/products/data/providers/product_category_usecase_providers.dart';
import 'package:intellicoffee/features/products/data/repositories/product_category_repository_impl.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/domain/repositories/product_category_repository.dart';
import 'package:intellicoffee/features/products/presentation/controllers/product_category_notifier.dart';
import 'package:intellicoffee/features/products/presentation/controllers/product_category_state.dart';

/// Provider para o repositório de categorias de produto
final productCategoryRepositoryProvider = Provider<ProductCategoryRepository>((ref) {
  return ProductCategoryRepositoryImpl(
    firestore: FirebaseFirestore.instance,
  );
});

/// Provider principal para gerenciamento de estado de categorias
final productCategoryNotifierProvider = StateNotifierProvider<ProductCategoryNotifier, ProductCategoryState>((ref) {
  final getUseCase = ref.watch(getProductCategoriesUseCaseProvider);
  final manageUseCase = ref.watch(manageProductCategoryUseCaseProvider);
  return ProductCategoryNotifier(getUseCase, manageUseCase);
});

/// Provider para obter todas as categorias (backward compatibility)
final allProductCategoriesProvider = FutureProvider<List<ProductCategory>>((ref) async {
  final notifier = ref.read(productCategoryNotifierProvider.notifier);
  await notifier.loadAllCategories();
  return ref.watch(productCategoryNotifierProvider).categories;
});

/// Provider para obter categorias de produto por tipo (backward compatibility)
final productCategoriesByTypeProvider = FutureProvider.family<List<ProductCategory>, ProductType>((ref, type) async {
  final notifier = ref.read(productCategoryNotifierProvider.notifier);
  await notifier.loadCategoriesByType(type);
  return ref.watch(productCategoryNotifierProvider).getCategoriesByType(type);
});

/// Provider para obter uma categoria de produto pelo ID (backward compatibility)
final productCategoryByIdProvider = FutureProvider.family<ProductCategory?, String>((ref, id) async {
  final notifier = ref.read(productCategoryNotifierProvider.notifier);
  await notifier.loadCategoryById(id);
  return ref.watch(productCategoryNotifierProvider).getCategoryById(id);
});

/// Provider para o estado da categoria atual em edição (backward compatibility)
final currentProductCategoryProvider = StateProvider<ProductCategory?>((ref) {
  return ref.watch(productCategoryNotifierProvider).currentCategory;
});

/// Provider para controlar o estado de carregamento (backward compatibility)
final productCategoryLoadingProvider = StateProvider<bool>((ref) {
  return ref.watch(productCategoryNotifierProvider).isLoading;
});

/// Provider para controlar o estado de erro (backward compatibility)
final productCategoryErrorProvider = StateProvider<String?>((ref) {
  return ref.watch(productCategoryNotifierProvider).error;
});

/// Providers convenientes para acesso direto aos dados

/// Provider para obter apenas categorias ativas
final activeProductCategoriesProvider = Provider<List<ProductCategory>>((ref) {
  return ref.watch(productCategoryNotifierProvider).activeCategories;
});

/// Provider para verificar se há erro
final productCategoryHasErrorProvider = Provider<bool>((ref) {
  return ref.watch(productCategoryNotifierProvider).hasError;
});

/// Provider para verificar se há mensagem de sucesso
final productCategoryHasSuccessProvider = Provider<bool>((ref) {
  return ref.watch(productCategoryNotifierProvider).hasSuccess;
});

/// Provider para obter mensagem de sucesso
final productCategorySuccessMessageProvider = Provider<String?>((ref) {
  return ref.watch(productCategoryNotifierProvider).successMessage;
}); 