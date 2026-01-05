import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/auth/data/services/admin_auth_service.dart';

/// Provider para o serviço de autenticação administrativa
final adminAuthServiceProvider = Provider<AdminAuthService>((ref) {
  return AdminAuthService();
});