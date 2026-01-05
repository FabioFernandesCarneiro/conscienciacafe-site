import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/auth/data/providers/auth_provider.dart';
import 'package:intellicoffee/features/auth/domain/models/app_user.dart';

/// Provedor que mapeia o usuário do Firebase para o modelo AppUser
final appUserProvider = Provider<AppUser?>((ref) {
  final authState = ref.watch(authStateProvider);
  
  return authState.when(
    data: (user) => user != null ? AppUser.fromFirebaseUser(user) : null,
    loading: () => null,
    error: (_, __) => null,
  );
});

/// Provedor que indica se existe um usuário logado
final isUserLoggedInProvider = Provider<bool>((ref) {
  final user = ref.watch(appUserProvider);
  return user != null;
});

/// Provedor que fornece o ID do usuário atual
final userIdProvider = Provider<String?>((ref) {
  final user = ref.watch(appUserProvider);
  return user?.uid;
});

/// Provedor que indica se o usuário atual é administrador
final isAdminProvider = Provider<bool>((ref) {
  final user = ref.watch(appUserProvider);
  return user?.isAdmin ?? false;
});

/// Provedor que indica se o usuário atual é funcionário
final isStaffProvider = Provider<bool>((ref) {
  final user = ref.watch(appUserProvider);
  return user?.isStaff ?? false;
});