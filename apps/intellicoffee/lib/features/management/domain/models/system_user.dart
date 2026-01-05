import 'package:cloud_firestore/cloud_firestore.dart';

/// Enumeração das funções disponíveis no sistema
enum UserRole {
  admin,    // Administrador com acesso completo
  gerente,  // Gerente com acesso amplo
  barista,  // Barista com acesso à torrefação e atendimento
  atendente // Atendente com acesso ao módulo de atendimento
}

/// Extensão para converter UserRole para String
extension UserRoleExtension on UserRole {
  String get displayName {
    switch (this) {
      case UserRole.admin:
        return 'Admin';
      case UserRole.gerente:
        return 'Gerente';
      case UserRole.barista:
        return 'Barista';
      case UserRole.atendente:
        return 'Atendente';
    }
  }
  
  /// Método para obter a cor associada à função
  int get color {
    switch (this) {
      case UserRole.admin:
        return 0xFF4CAF50; // Verde
      case UserRole.gerente:
        return 0xFF2196F3; // Azul
      case UserRole.barista:
        return 0xFFF57C00; // Âmbar
      case UserRole.atendente:
        return 0xFFE67E22; // Laranja
    }
  }
}

/// Modelo para usuários do sistema administrativo
class SystemUser {
  final String id;
  final String fullName;
  final String email;
  final String? phone;
  final String username;
  final UserRole role;
  final bool isActive;
  final String? photoUrl;
  final Map<String, bool> moduleAccess;
  final String? notes;
  final DateTime createdAt;
  final DateTime? lastModifiedAt;

  SystemUser({
    required this.id,
    required this.fullName,
    required this.email,
    this.phone,
    required this.username,
    required this.role,
    this.isActive = true,
    this.photoUrl,
    required this.moduleAccess,
    this.notes,
    required this.createdAt,
    this.lastModifiedAt,
  });

  /// Obter iniciais do nome para exibição no avatar
  String get initials {
    if (fullName.isNotEmpty) {
      final nameParts = fullName.split(' ');
      if (nameParts.length > 1) {
        return '${nameParts.first[0]}${nameParts.last[0]}'.toUpperCase();
      }
      return nameParts.first[0].toUpperCase();
    }
    return email[0].toUpperCase();
  }

  /// Cria uma cópia do objeto com os campos atualizados
  SystemUser copyWith({
    String? id,
    String? fullName,
    String? email,
    String? phone,
    String? username,
    UserRole? role,
    bool? isActive,
    String? photoUrl,
    Map<String, bool>? moduleAccess,
    String? notes,
    DateTime? createdAt,
    DateTime? lastModifiedAt,
  }) {
    return SystemUser(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      email: email ?? this.email,
      phone: phone ?? this.phone,
      username: username ?? this.username,
      role: role ?? this.role,
      isActive: isActive ?? this.isActive,
      photoUrl: photoUrl ?? this.photoUrl,
      moduleAccess: moduleAccess ?? this.moduleAccess,
      notes: notes ?? this.notes,
      createdAt: createdAt ?? this.createdAt,
      lastModifiedAt: lastModifiedAt ?? this.lastModifiedAt,
    );
  }

  /// Factory para criar um SystemUser a partir de um documento do Firestore
  factory SystemUser.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    
    // Converte o campo 'moduleAccess' de Map<String, dynamic> para Map<String, bool>
    final Map<String, dynamic> accessData = data['moduleAccess'] ?? {};
    final Map<String, bool> moduleAccess = {};
    
    accessData.forEach((key, value) {
      moduleAccess[key] = value as bool;
    });
    
    return SystemUser(
      id: doc.id,
      fullName: data['fullName'] ?? '',
      email: data['email'] ?? '',
      phone: data['phone'],
      username: data['username'] ?? '',
      role: _parseRole(data['role']),
      isActive: data['isActive'] ?? true,
      photoUrl: data['photoUrl'],
      moduleAccess: moduleAccess,
      notes: data['notes'],
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      lastModifiedAt: (data['lastModifiedAt'] as Timestamp?)?.toDate(),
    );
  }

  /// Converte o objeto para um Map para salvar no Firestore
  Map<String, dynamic> toFirestore() {
    return {
      'fullName': fullName,
      'email': email,
      'phone': phone,
      'username': username,
      'role': role.name,
      'isActive': isActive,
      'photoUrl': photoUrl,
      'moduleAccess': moduleAccess,
      'notes': notes,
      'createdAt': Timestamp.fromDate(createdAt),
      'lastModifiedAt': lastModifiedAt != null 
          ? Timestamp.fromDate(lastModifiedAt!) 
          : Timestamp.fromDate(DateTime.now()),
    };
  }
  
  /// Helper para converter string em UserRole
  static UserRole _parseRole(String? roleName) {
    if (roleName == null) return UserRole.atendente;
    
    try {
      return UserRole.values.firstWhere(
        (role) => role.name.toLowerCase() == roleName.toLowerCase(),
        orElse: () => UserRole.atendente,
      );
    } catch (_) {
      return UserRole.atendente;
    }
  }
  
  /// Factory para criar um novo usuário vazio (para formulários)
  factory SystemUser.empty() {
    return SystemUser(
      id: '',
      fullName: '',
      email: '',
      username: '',
      role: UserRole.atendente,
      moduleAccess: {
        'atendimento': true,
        'clientes': false,
        'torrefacao': false,
        'vendasB2B': false,
        'eventos': false,
        'gestao': false,
      },
      createdAt: DateTime.now(),
    );
  }
}