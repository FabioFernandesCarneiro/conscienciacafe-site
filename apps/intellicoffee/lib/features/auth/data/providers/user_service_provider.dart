import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/auth/data/services/user_service.dart';

/// Provider para o serviço de usuário
final userServiceProvider = Provider<UserService>((ref) {
  return UserService();
});