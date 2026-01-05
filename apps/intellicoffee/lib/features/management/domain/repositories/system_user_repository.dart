import 'package:intellicoffee/features/management/domain/models/system_user.dart';

/// Interface para o repositório de usuários do sistema
abstract class SystemUserRepository {
  /// Obter todos os usuários do sistema
  Future<List<SystemUser>> getAllUsers();
  
  /// Obter usuários ativos
  Future<List<SystemUser>> getActiveUsers();
  
  /// Obter usuários inativos
  Future<List<SystemUser>> getInactiveUsers();
  
  /// Obter um usuário por ID
  Future<SystemUser?> getUserById(String id);
  
  /// Criar um novo usuário
  /// Se a senha for fornecida, também cria o usuário no Firebase Authentication
  Future<String> createUser(SystemUser user, {String? password});
  
  /// Atualizar um usuário existente
  Future<void> updateUser(SystemUser user);
  
  /// Excluir um usuário
  Future<void> deleteUser(String id);
  
  /// Ativar ou desativar um usuário
  Future<void> toggleUserStatus(String id, bool isActive);
}