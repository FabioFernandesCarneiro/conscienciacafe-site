/// Classe base para erros customizados da aplicação
abstract class AppError implements Exception {
  final String message;
  final String? code;
  final dynamic originalError;
  final StackTrace? stackTrace;

  const AppError({
    required this.message,
    this.code,
    this.originalError,
    this.stackTrace,
  });

  @override
  String toString() => 'AppError: $message (code: $code)';
}

/// Erro de rede/conectividade
class NetworkError extends AppError {
  const NetworkError({
    required super.message,
    super.code,
    super.originalError,
    super.stackTrace,
  });

  factory NetworkError.connectionTimeout() {
    return const NetworkError(
      message: 'Tempo limite de conexão excedido',
      code: 'NETWORK_TIMEOUT',
    );
  }

  factory NetworkError.noConnection() {
    return const NetworkError(
      message: 'Sem conexão com a internet',
      code: 'NO_CONNECTION',
    );
  }

  factory NetworkError.serverError() {
    return const NetworkError(
      message: 'Erro no servidor',
      code: 'SERVER_ERROR',
    );
  }
}

/// Erro de autenticação
class AuthError extends AppError {
  const AuthError({
    required super.message,
    super.code,
    super.originalError,
    super.stackTrace,
  });

  factory AuthError.invalidCredentials() {
    return const AuthError(
      message: 'Credenciais inválidas',
      code: 'INVALID_CREDENTIALS',
    );
  }

  factory AuthError.sessionExpired() {
    return const AuthError(
      message: 'Sessão expirada',
      code: 'SESSION_EXPIRED',
    );
  }

  factory AuthError.unauthorized() {
    return const AuthError(
      message: 'Não autorizado',
      code: 'UNAUTHORIZED',
    );
  }
}

/// Erro de validação
class ValidationError extends AppError {
  final Map<String, String> fieldErrors;

  const ValidationError({
    required super.message,
    this.fieldErrors = const {},
    super.code,
    super.originalError,
    super.stackTrace,
  });

  factory ValidationError.required(String field) {
    return ValidationError(
      message: 'Campo obrigatório: $field',
      code: 'FIELD_REQUIRED',
      fieldErrors: {field: 'Campo obrigatório'},
    );
  }

  factory ValidationError.invalid(String field, String reason) {
    return ValidationError(
      message: 'Campo inválido: $field ($reason)',
      code: 'FIELD_INVALID',
      fieldErrors: {field: reason},
    );
  }
}

/// Erro de dados/repositório
class DataError extends AppError {
  const DataError({
    required super.message,
    super.code,
    super.originalError,
    super.stackTrace,
  });

  factory DataError.notFound(String resource) {
    return DataError(
      message: '$resource não encontrado',
      code: 'NOT_FOUND',
    );
  }

  factory DataError.alreadyExists(String resource) {
    return DataError(
      message: '$resource já existe',
      code: 'ALREADY_EXISTS',
    );
  }

  factory DataError.permissionDenied() {
    return const DataError(
      message: 'Permissão negada',
      code: 'PERMISSION_DENIED',
    );
  }
}

/// Erro genérico da aplicação
class GenericAppError extends AppError {
  const GenericAppError({
    required super.message,
    super.code,
    super.originalError,
    super.stackTrace,
  });

  factory GenericAppError.unknown(dynamic error) {
    return GenericAppError(
      message: 'Erro inesperado: ${error.toString()}',
      code: 'UNKNOWN_ERROR',
      originalError: error,
    );
  }
}