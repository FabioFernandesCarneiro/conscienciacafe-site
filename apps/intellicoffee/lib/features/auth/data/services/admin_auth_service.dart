import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:cloud_functions/cloud_functions.dart';

/// Serviço para gerenciar operações administrativas de autenticação
/// Usado para criar/modificar usuários sem afetar a sessão atual
class AdminAuthService {
  // final UserService _userService = UserService(); // TODO: implementar quando necessário
  final FirebaseFunctions _functions;
  
  AdminAuthService({FirebaseFunctions? functions}) 
    : _functions = functions ?? FirebaseFunctions.instance;
  
  /// Verifica se um usuário com o email fornecido existe no Firebase Auth
  Future<bool> userExistsInAuth(String email) async {
    try {
      // NOTA: fetchSignInMethodsForEmail foi deprecated por questões de segurança
      // Para verificar se um usuário existe, agora é recomendado tentar fazer login
      // ou usar o Admin SDK em uma Cloud Function
      
      // Por enquanto, vamos retornar false e deixar o Firebase Auth
      // retornar o erro apropriado durante a criação
      return false;
      
      // Código anterior (deprecated):
      // final methods = await FirebaseAuth.instance.fetchSignInMethodsForEmail(email);
      // return methods.isNotEmpty;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Erro ao verificar se o usuário existe: $e');
      }
      return false;
    }
  }

  /// Exclui um usuário do Firebase Auth pelo e-mail
  /// Nota: Esta operação normalmente requer o Admin SDK
  Future<bool> deleteUserByEmail(String email) async {
    try {
      // 1. Verificar se o e-mail existe no Auth
      final existsInAuth = await userExistsInAuth(email);
      if (!existsInAuth) {
        if (kDebugMode) {
          debugPrint('Usuário não encontrado no Firebase Auth: $email');
        }
        return false;
      }

      // 2. Como não podemos excluir usuários diretamente sem o Admin SDK,
      // vamos adicionar uma nota de aviso para o desenvolvedor
      if (kDebugMode) {
        debugPrint('==========================================================');
        debugPrint('AVISO: Não é possível excluir o usuário $email do Firebase Auth');
        debugPrint('usando o SDK Flutter normal.');
        debugPrint('');
        debugPrint('SOLUÇÃO:');
        debugPrint('1) Atualize seu projeto para o plano Blaze do Firebase');
        debugPrint('2) Faça o deploy da Cloud Function "deleteUser"');
        debugPrint('3) Mude a flag "useCloudFunction" para true em SystemUserRepositoryImpl');
        debugPrint('==========================================================');
      }
      
      // Retornar que não pudemos excluir o usuário
      return false;
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Erro ao excluir usuário do Firebase Auth: $e');
      }
      return false;
    }
  }
  
  /// Cria um novo usuário no Firebase Auth sem fazer login automaticamente
  /// Usa Cloud Function para não afetar a sessão atual
  Future<String?> createUser({
    required String email,
    required String password,
    String? displayName,
    bool checkExistingEmail = true,
  }) async {
    try {
      // Verificar se o e-mail já está em uso (opcional se a função já faz isso)
      if (checkExistingEmail) {
        final exists = await userExistsInAuth(email);
        if (exists) {
          if (kDebugMode) {
            debugPrint('Email já está em uso no Firebase Auth: $email');
          }
          throw FirebaseAuthException(
            code: 'email-already-in-use',
            message: 'O email já está sendo usado por outra conta.'
          );
        }
      }
      
      if (kDebugMode) {
        debugPrint('Criando usuário no Firebase Auth usando Cloud Function: $email');
      }
      
      try {
        // Chamar a Cloud Function para criar o usuário
        // Isso não afeta a sessão atual do usuário no app
        final result = await _functions.httpsCallable('createUser').call({
          'email': email,
          'password': password,
          'displayName': displayName,
        });
        
        if (kDebugMode) {
          debugPrint('Resultado da criação via Cloud Function: ${result.data}');
        }
        
        // Extrair o UID do usuário criado da resposta
        final uid = result.data['uid'] as String?;
        
        if (uid == null) {
          throw Exception('UID não retornado pela função.');
        }
        
        if (kDebugMode) {
          debugPrint('Usuário criado com UID: $uid');
          debugPrint('Sessão atual preservada!');
        }
        
        return uid;
      } catch (functionError) {
        if (kDebugMode) {
          debugPrint('Erro ao chamar Cloud Function para criar usuário: $functionError');
          debugPrint('Detalhes: ${functionError.toString()}');
        }
        
        // Repassar a mensagem de erro da função
        if (functionError is FirebaseFunctionsException) {
          throw Exception(functionError.message);
        }
        
        throw Exception('Falha ao criar usuário: $functionError');
      }
    } on FirebaseAuthException catch (e) {
      if (kDebugMode) {
        debugPrint('Erro ao criar usuário no Firebase Auth: ${e.code} - ${e.message}');
      }
      throw Exception(_getFirebaseErrorMessage(e.code));
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Erro inesperado ao criar usuário: $e');
      }
      throw Exception('Não foi possível criar o usuário: $e');
    }
  }
  
  /// Obter mensagem de erro amigável com base no código do Firebase
  String _getFirebaseErrorMessage(String errorCode) {
    switch (errorCode) {
      case 'email-already-in-use':
        return 'Este e-mail já está sendo usado por outra conta.';
      case 'invalid-email':
        return 'O e-mail fornecido é inválido.';
      case 'operation-not-allowed':
        return 'O cadastro com e-mail e senha não está habilitado.';
      case 'weak-password':
        return 'A senha é muito fraca. Escolha uma senha mais forte.';
      default:
        return 'Erro ao criar usuário: $errorCode';
    }
  }
}