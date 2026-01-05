import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/products/domain/models/product_category.dart';
import 'package:intellicoffee/features/products/domain/repositories/product_category_repository.dart';

class ProductCategoryRepositoryImpl implements ProductCategoryRepository {
  final FirebaseFirestore _firestore;
  
  ProductCategoryRepositoryImpl({
    FirebaseFirestore? firestore,
  }) : _firestore = firestore ?? FirebaseFirestore.instance;
  
  /// Referência para a coleção de categorias
  CollectionReference<Map<String, dynamic>> get _categoriesRef => 
      _firestore.collection(AppConstants.colProductCategories);
  
  @override
  Future<List<ProductCategory>> getAllCategories() async {
    try {
      final snapshot = await _categoriesRef
          .orderBy('order')
          .get();
      
      return snapshot.docs
          .map((doc) => ProductCategory.fromFirestore(doc))
          .toList();
    } catch (e) {
      debugPrint('Erro ao obter categorias: $e');
      return [];
    }
  }
  
  @override
  Future<List<ProductCategory>> getCategoriesByType(ProductType type) async {
    try {
      final snapshot = await _categoriesRef
          .where('productType', isEqualTo: type.name)
          .orderBy('order')
          .get();
      
      return snapshot.docs
          .map((doc) => ProductCategory.fromFirestore(doc))
          .toList();
    } catch (e) {
      debugPrint('Erro ao obter categorias por tipo: $e');
      return [];
    }
  }
  
  @override
  Future<ProductCategory?> getCategoryById(String id) async {
    try {
      final doc = await _categoriesRef.doc(id).get();
      if (!doc.exists) return null;
      
      return ProductCategory.fromFirestore(doc);
    } catch (e) {
      debugPrint('Erro ao obter categoria: $e');
      return null;
    }
  }
  
  @override
  Future<String> addCategory(ProductCategory category) async {
    try {
      // Verificar ordem máxima atual
      int maxOrder = 0;
      final snapshot = await _categoriesRef.get();
      for (var doc in snapshot.docs) {
        final order = doc.data()['order'] as int? ?? 0;
        if (order > maxOrder) maxOrder = order;
      }
      
      // Criar uma nova categoria com ordem = maxOrder + 1
      final updatedCategory = category.copyWith(
        order: maxOrder + 1,
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );
      
      // Adicionar ao Firestore
      final docRef = await _categoriesRef.add(updatedCategory.toFirestore());
      return docRef.id;
    } catch (e) {
      debugPrint('Erro ao adicionar categoria: $e');
      throw Exception('Não foi possível adicionar a categoria');
    }
  }
  
  @override
  Future<void> updateCategory(ProductCategory category) async {
    try {
      await _categoriesRef.doc(category.id).update({
        'name': category.name,
        'productType': category.productType.name,
        'description': category.description,
        'isActive': category.isActive,
        'customFields': category.customFields.map((field) => field.toMap()).toList(),
        'updatedAt': Timestamp.fromDate(DateTime.now()),
      });
    } catch (e) {
      debugPrint('Erro ao atualizar categoria: $e');
      throw Exception('Não foi possível atualizar a categoria');
    }
  }
  
  @override
  Future<void> deleteCategory(String id) async {
    try {
      await _categoriesRef.doc(id).delete();
    } catch (e) {
      debugPrint('Erro ao excluir categoria: $e');
      throw Exception('Não foi possível excluir a categoria');
    }
  }
  
  @override
  Future<void> updateCategoriesOrder(List<String> categoryIds) async {
    try {
      final batch = _firestore.batch();
      
      for (int i = 0; i < categoryIds.length; i++) {
        final categoryId = categoryIds[i];
        final categoryRef = _categoriesRef.doc(categoryId);
        
        batch.update(categoryRef, {
          'order': i,
          'updatedAt': Timestamp.fromDate(DateTime.now()),
        });
      }
      
      await batch.commit();
    } catch (e) {
      debugPrint('Erro ao atualizar ordem das categorias: $e');
      throw Exception('Não foi possível atualizar a ordem das categorias');
    }
  }
  
  @override
  Future<void> toggleCategoryActive(String id, bool isActive) async {
    try {
      await _categoriesRef.doc(id).update({
        'isActive': isActive,
        'updatedAt': Timestamp.fromDate(DateTime.now()),
      });
    } catch (e) {
      debugPrint('Erro ao alterar status da categoria: $e');
      throw Exception('Não foi possível alterar o status da categoria');
    }
  }
} 