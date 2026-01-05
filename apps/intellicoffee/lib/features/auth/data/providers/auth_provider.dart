import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/auth/data/services/auth_service.dart';

// Provedor para o serviço de autenticação
final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});

// Provedor para o estado de autenticação (stream)
final authStateProvider = StreamProvider<User?>((ref) {
  final authService = ref.watch(authServiceProvider);
  return authService.authStateChanges;
});

// Provedor para o usuário atual
final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.when(
    data: (user) => user,
    loading: () => null,
    error: (_, __) => null,
  );
});

// Provedor para verificar se o usuário está logado
final isLoggedInProvider = Provider<bool>((ref) {
  final user = ref.watch(currentUserProvider);
  return user != null;
});

// Provedor para notificar quando a sessão pode ter sido perdida durante operações administrativas
final sessionLostNotifierProvider = StateNotifierProvider<SessionLostNotifier, bool>((ref) {
  return SessionLostNotifier();
});

// Notificador para controlar o estado de sessão perdida
class SessionLostNotifier extends StateNotifier<bool> {
  SessionLostNotifier() : super(false);
  
  // Define que a sessão foi perdida e precisa ser refeita
  void notifySessionLost() {
    state = true;
  }
  
  // Reseta o estado após o usuário ser notificado
  void resetNotification() {
    state = false;
  }
}