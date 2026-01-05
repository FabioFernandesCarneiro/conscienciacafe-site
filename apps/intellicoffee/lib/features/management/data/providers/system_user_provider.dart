import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/management/data/repositories/system_user_repository_impl.dart';
import 'package:intellicoffee/features/management/domain/models/system_user.dart';
import 'package:intellicoffee/features/management/domain/repositories/system_user_repository.dart';

/// Provider para o repositório de usuários do sistema
final systemUserRepositoryProvider = Provider<SystemUserRepository>((ref) {
  return SystemUserRepositoryImpl();
});

/// Enumeração para os tipos de filtragem de usuários
enum UserFilter {
  all,
  active,
  inactive,
}

/// Provider para o estado da lista de usuários
final usersProvider = StateNotifierProvider<UsersNotifier, AsyncValue<List<SystemUser>>>((ref) {
  final repository = ref.watch(systemUserRepositoryProvider);
  return UsersNotifier(repository);
});

/// Provider para o filtro atual
final userFilterProvider = StateProvider<UserFilter>((ref) {
  return UserFilter.all;
});

/// Provider para o termo de busca de usuários
final userSearchTermProvider = StateProvider<String>((ref) => '');

/// Provider para a lista filtrada de usuários
final filteredUsersProvider = Provider<AsyncValue<List<SystemUser>>>((ref) {
  final users = ref.watch(usersProvider);
  final filter = ref.watch(userFilterProvider);
  final searchTerm = ref.watch(userSearchTermProvider).trim().toLowerCase();
  
  return users.when(
    data: (data) {
      // Primeiro aplicamos o filtro de status
      List<SystemUser> filteredByStatus;
      switch (filter) {
        case UserFilter.all:
          filteredByStatus = List.from(data);
          break;
        case UserFilter.active:
          filteredByStatus = data.where((user) => user.isActive).toList();
          break;
        case UserFilter.inactive:
          filteredByStatus = data.where((user) => !user.isActive).toList();
          break;
      }
      
      // Se não há termo de busca, retornamos apenas o filtro por status
      if (searchTerm.isEmpty) {
        return AsyncValue.data(filteredByStatus);
      }
      
      // Aplicamos o filtro de busca por nome, email ou username
      final filteredResults = filteredByStatus.where((user) {
        return user.fullName.toLowerCase().contains(searchTerm) || 
               user.email.toLowerCase().contains(searchTerm) ||
               user.username.toLowerCase().contains(searchTerm);
      }).toList();
      
      return AsyncValue.data(filteredResults);
    },
    loading: () => const AsyncValue.loading(),
    error: (error, stackTrace) => AsyncValue.error(error, stackTrace),
  );
});

/// Notifier para gerenciar o estado da lista de usuários
class UsersNotifier extends StateNotifier<AsyncValue<List<SystemUser>>> {
  final SystemUserRepository _repository;
  
  UsersNotifier(this._repository) : super(const AsyncValue.loading()) {
    loadUsers();
  }
  
  /// Carregar todos os usuários
  Future<void> loadUsers() async {
    try {
      state = const AsyncValue.loading();
      final users = await _repository.getAllUsers();
      state = AsyncValue.data(users);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }
  
  /// Criar um novo usuário
  Future<String> createUser(SystemUser user, {String? password}) async {
    try {
      // Passamos a senha para o repositório para criar o usuário no Firebase Auth
      final id = await _repository.createUser(user, password: password);
      await loadUsers(); // Recarregar lista
      return id;
    } catch (error) {
      // Rethrow para o caller lidar com a exceção
      rethrow;
    }
  }
  
  /// Atualizar um usuário existente
  Future<void> updateUser(SystemUser user) async {
    try {
      await _repository.updateUser(user);
      await loadUsers(); // Recarregar lista
    } catch (error) {
      rethrow;
    }
  }
  
  /// Excluir um usuário
  Future<void> deleteUser(String id) async {
    try {
      await _repository.deleteUser(id);
      await loadUsers(); // Recarregar lista
    } catch (error) {
      rethrow;
    }
  }
  
  /// Ativar ou desativar um usuário
  Future<void> toggleUserStatus(String id, bool isActive) async {
    try {
      await _repository.toggleUserStatus(id, isActive);
      await loadUsers(); // Recarregar lista
    } catch (error) {
      rethrow;
    }
  }
}