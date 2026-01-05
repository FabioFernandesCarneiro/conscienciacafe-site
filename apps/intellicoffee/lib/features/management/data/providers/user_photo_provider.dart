import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/management/data/services/user_photo_service.dart';

/// Provider para o serviço de fotos de usuário
final userPhotoServiceProvider = Provider<UserPhotoService>((ref) {
  return UserPhotoService();
});