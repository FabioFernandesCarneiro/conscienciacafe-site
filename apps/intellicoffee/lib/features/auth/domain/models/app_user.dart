import 'package:firebase_auth/firebase_auth.dart';

/// Modelo de usuário da aplicação
/// Encapsula os dados do usuário do Firebase Auth
class AppUser {
  final String uid;
  final String? email;
  final String? displayName;
  final String? photoURL;
  final bool isEmailVerified;
  final DateTime? createdAt;
  final DateTime? lastLoginAt;
  final Map<String, dynamic>? customClaims;

  AppUser({
    required this.uid,
    this.email,
    this.displayName,
    this.photoURL,
    this.isEmailVerified = false,
    this.createdAt,
    this.lastLoginAt,
    this.customClaims,
  });

  /// Factory para criar um AppUser a partir de um FirebaseUser
  factory AppUser.fromFirebaseUser(User user) {
    return AppUser(
      uid: user.uid,
      email: user.email,
      displayName: user.displayName,
      photoURL: user.photoURL,
      isEmailVerified: user.emailVerified,
      // Metadata pode ser nulo em alguns casos
      createdAt: user.metadata.creationTime,
      lastLoginAt: user.metadata.lastSignInTime,
    );
  }

  /// Verificar se o usuário é admin
  bool get isAdmin => customClaims != null && customClaims!['admin'] == true;

  /// Verificar se o usuário é staff
  bool get isStaff => customClaims != null && customClaims!['staff'] == true;

  /// Obter iniciais do nome do usuário
  String get initials {
    if (displayName != null && displayName!.isNotEmpty) {
      final nameParts = displayName!.split(' ');
      if (nameParts.length > 1) {
        return '${nameParts.first[0]}${nameParts.last[0]}'.toUpperCase();
      }
      return nameParts.first[0].toUpperCase();
    }
    return email != null ? email![0].toUpperCase() : 'U';
  }

  /// Cria uma cópia do objeto com os campos atualizados
  AppUser copyWith({
    String? uid,
    String? email,
    String? displayName,
    String? photoURL,
    bool? isEmailVerified,
    DateTime? createdAt,
    DateTime? lastLoginAt,
    Map<String, dynamic>? customClaims,
  }) {
    return AppUser(
      uid: uid ?? this.uid,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      photoURL: photoURL ?? this.photoURL,
      isEmailVerified: isEmailVerified ?? this.isEmailVerified,
      createdAt: createdAt ?? this.createdAt,
      lastLoginAt: lastLoginAt ?? this.lastLoginAt,
      customClaims: customClaims ?? this.customClaims,
    );
  }
}