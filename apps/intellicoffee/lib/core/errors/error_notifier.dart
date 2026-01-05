import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/core/errors/app_error.dart';
import 'package:intellicoffee/core/errors/error_handler.dart';

/// Estado para notificações de erro globais
class ErrorNotificationState {
  final AppError? currentError;
  final bool isVisible;

  const ErrorNotificationState({
    this.currentError,
    this.isVisible = false,
  });

  ErrorNotificationState copyWith({
    AppError? currentError,
    bool? isVisible,
  }) {
    return ErrorNotificationState(
      currentError: currentError ?? this.currentError,
      isVisible: isVisible ?? this.isVisible,
    );
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is ErrorNotificationState &&
        other.currentError == currentError &&
        other.isVisible == isVisible;
  }

  @override
  int get hashCode => currentError.hashCode ^ isVisible.hashCode;
}

/// Notifier para gerenciar erros globais da aplicação
class ErrorNotifier extends StateNotifier<ErrorNotificationState> {
  ErrorNotifier() : super(const ErrorNotificationState());

  /// Exibe um erro para o usuário
  void showError(dynamic error, [StackTrace? stackTrace]) {
    final appError = AppErrorHandler.handleError(error, stackTrace);
    
    state = state.copyWith(
      currentError: appError,
      isVisible: true,
    );
  }

  /// Limpa o erro atual
  void clearError() {
    state = state.copyWith(
      currentError: null,
      isVisible: false,
    );
  }

  /// Obtém a mensagem para exibir ao usuário
  String? get displayMessage {
    if (state.currentError == null) return null;
    return AppErrorHandler.getDisplayMessage(state.currentError!);
  }

  /// Verifica se o erro atual pode ser resolvido tentando novamente
  bool get canRetry {
    if (state.currentError == null) return false;
    return AppErrorHandler.canRetry(state.currentError!);
  }

  /// Verifica se o erro requer nova autenticação
  bool get requiresReauth {
    if (state.currentError == null) return false;
    return AppErrorHandler.requiresReauth(state.currentError!);
  }
}

/// Provider global para notificações de erro
final errorNotifierProvider = StateNotifierProvider<ErrorNotifier, ErrorNotificationState>((ref) {
  return ErrorNotifier();
});

/// Provider conveniente para acessar apenas o erro atual
final currentErrorProvider = Provider<AppError?>((ref) {
  return ref.watch(errorNotifierProvider).currentError;
});

/// Provider conveniente para verificar se há erro visível
final hasVisibleErrorProvider = Provider<bool>((ref) {
  return ref.watch(errorNotifierProvider).isVisible;
});

/// Provider conveniente para obter a mensagem de erro para exibição
final errorMessageProvider = Provider<String?>((ref) {
  return ref.watch(errorNotifierProvider.notifier).displayMessage;
});

/// Provider conveniente para verificar se pode tentar novamente
final canRetryErrorProvider = Provider<bool>((ref) {
  return ref.watch(errorNotifierProvider.notifier).canRetry;
});

/// Provider conveniente para verificar se requer reautenticação
final requiresReauthProvider = Provider<bool>((ref) {
  return ref.watch(errorNotifierProvider.notifier).requiresReauth;
});