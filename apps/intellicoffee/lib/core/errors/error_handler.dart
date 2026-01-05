import 'dart:developer' as developer;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:intellicoffee/core/errors/app_error.dart';

/// Handler global para tratamento e conversão de erros
class AppErrorHandler {
  static const String _logTag = 'AppErrorHandler';

  /// Converte exceções do sistema para erros customizados da aplicação
  static AppError handleError(dynamic error, [StackTrace? stackTrace]) {
    AppError appError;

    // Tratamento específico por tipo de erro
    if (error is AppError) {
      appError = error;
    } else if (error is FirebaseAuthException) {
      appError = _handleFirebaseAuthError(error);
    } else if (error is FirebaseException) {
      appError = _handleFirebaseError(error);
    } else {
      appError = GenericAppError.unknown(error);
    }

    // Log do erro
    _logError(appError, stackTrace);

    return appError;
  }

  /// Trata erros de autenticação do Firebase
  static AuthError _handleFirebaseAuthError(FirebaseAuthException error) {
    switch (error.code) {
      case 'user-not-found':
      case 'wrong-password':
      case 'invalid-credential':
        return AuthError.invalidCredentials();
      
      case 'user-disabled':
        return const AuthError(
          message: 'Conta desabilitada',
          code: 'USER_DISABLED',
        );
      
      case 'too-many-requests':
        return const AuthError(
          message: 'Muitas tentativas. Tente novamente mais tarde',
          code: 'TOO_MANY_REQUESTS',
        );
      
      case 'network-request-failed':
        return const AuthError(
          message: 'Sem conexão com a internet',
          code: 'NO_CONNECTION',
        );
      
      case 'email-already-in-use':
        return const AuthError(
          message: 'E-mail já está em uso',
          code: 'EMAIL_IN_USE',
        );
      
      case 'weak-password':
        return const AuthError(
          message: 'Senha muito fraca',
          code: 'WEAK_PASSWORD',
        );
      
      case 'invalid-email':
        return const AuthError(
          message: 'E-mail inválido',
          code: 'INVALID_EMAIL',
        );
      
      default:
        return AuthError(
          message: error.message ?? 'Erro de autenticação',
          code: error.code,
          originalError: error,
        );
    }
  }

  /// Trata erros do Firestore
  static DataError _handleFirebaseError(FirebaseException error) {
    switch (error.code) {
      case 'permission-denied':
        return DataError.permissionDenied();
      
      case 'not-found':
        return DataError.notFound('Documento');
      
      case 'already-exists':
        return DataError.alreadyExists('Documento');
      
      case 'unavailable':
        return const DataError(
          message: 'Serviço temporariamente indisponível',
          code: 'SERVICE_UNAVAILABLE',
        );
      
      case 'deadline-exceeded':
        return const DataError(
          message: 'Tempo limite de conexão excedido',
          code: 'NETWORK_TIMEOUT',
        );
      
      default:
        return DataError(
          message: error.message ?? 'Erro na base de dados',
          code: error.code,
          originalError: error,
        );
    }
  }

  /// Faz log do erro
  static void _logError(AppError error, [StackTrace? stackTrace]) {
    if (kDebugMode) {
      developer.log(
        error.message,
        name: _logTag,
        error: error.originalError,
        stackTrace: stackTrace ?? error.stackTrace,
      );
    }
    
    // Aqui você pode adicionar integração com serviços de analytics
    // como Firebase Crashlytics, Sentry, etc.
    // _sendToAnalytics(error, stackTrace);
  }

  /// Obtém uma mensagem amigável para exibir ao usuário
  static String getDisplayMessage(AppError error) {
    // Mensagens específicas para códigos conhecidos
    switch (error.code) {
      case 'NO_CONNECTION':
        return 'Verifique sua conexão com a internet e tente novamente';
      
      case 'NETWORK_TIMEOUT':
        return 'A operação demorou muito para ser concluída. Tente novamente';
      
      case 'SESSION_EXPIRED':
        return 'Sua sessão expirou. Faça login novamente';
      
      case 'PERMISSION_DENIED':
        return 'Você não tem permissão para realizar esta ação';
      
      case 'INVALID_CREDENTIALS':
        return 'E-mail ou senha incorretos';
      
      case 'SERVICE_UNAVAILABLE':
        return 'Serviço temporariamente indisponível. Tente novamente em alguns instantes';
      
      default:
        return error.message;
    }
  }

  /// Determina se o erro pode ser resolvido tentando novamente
  static bool canRetry(AppError error) {
    const retryableCodes = {
      'NETWORK_TIMEOUT',
      'NO_CONNECTION',
      'SERVICE_UNAVAILABLE',
      'TOO_MANY_REQUESTS',
    };
    
    return retryableCodes.contains(error.code);
  }

  /// Determina se o erro requer nova autenticação
  static bool requiresReauth(AppError error) {
    const reauthCodes = {
      'SESSION_EXPIRED',
      'UNAUTHORIZED',
      'PERMISSION_DENIED',
    };
    
    return reauthCodes.contains(error.code);
  }
}