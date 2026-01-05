import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/auth/data/services/admin_auth_service.dart';
import 'package:intellicoffee/features/management/domain/models/system_user.dart';
import 'package:intellicoffee/features/management/domain/repositories/system_user_repository.dart';
import 'package:cloud_functions/cloud_functions.dart';

class SystemUserRepositoryImpl implements SystemUserRepository {
  final FirebaseFirestore _firestore;
  final AdminAuthService _adminAuthService;
  final FirebaseFunctions _functions;
  
  SystemUserRepositoryImpl({
    FirebaseFirestore? firestore,
    AdminAuthService? adminAuthService,
    FirebaseFunctions? functions,
  }) : 
    _firestore = firestore ?? FirebaseFirestore.instance,
    _adminAuthService = adminAuthService ?? AdminAuthService(),
    _functions = functions ?? FirebaseFunctions.instance;
  
  /// Referência para a coleção de usuários do sistema
  CollectionReference<Map<String, dynamic>> get _usersCollection => 
      _firestore.collection(AppConstants.colUsers);
  
  @override
  Future<List<SystemUser>> getAllUsers() async {
    final snapshot = await _usersCollection.get();
    return snapshot.docs.map((doc) => SystemUser.fromFirestore(doc)).toList();
  }
  
  @override
  Future<List<SystemUser>> getActiveUsers() async {
    final snapshot = await _usersCollection
        .where('isActive', isEqualTo: true)
        .get();
    return snapshot.docs.map((doc) => SystemUser.fromFirestore(doc)).toList();
  }
  
  @override
  Future<List<SystemUser>> getInactiveUsers() async {
    final snapshot = await _usersCollection
        .where('isActive', isEqualTo: false)
        .get();
    return snapshot.docs.map((doc) => SystemUser.fromFirestore(doc)).toList();
  }
  
  @override
  Future<SystemUser?> getUserById(String id) async {
    final doc = await _usersCollection.doc(id).get();
    if (!doc.exists) return null;
    return SystemUser.fromFirestore(doc);
  }
  
  @override
  Future<String> createUser(SystemUser user, {String? password}) async {
    // Verificar se já existe um usuário com o mesmo email ou username no Firestore
    final emailQuery = await _usersCollection
        .where('email', isEqualTo: user.email)
        .limit(1)
        .get();
    
    if (emailQuery.docs.isNotEmpty) {
      throw Exception('Email já está em uso no Firestore');
    }
    
    final usernameQuery = await _usersCollection
        .where('username', isEqualTo: user.username)
        .limit(1)
        .get();
    
    if (usernameQuery.docs.isNotEmpty) {
      throw Exception('Nome de usuário já está em uso');
    }
    
    // Verificar se o email já existe no Firebase Auth
    final existsInAuth = await _adminAuthService.userExistsInAuth(user.email);
    if (existsInAuth) {
      if (kDebugMode) {
        print('AVISO: Email ${user.email} já existe no Firebase Auth');
        print('Você estará criando um registro duplicado no Firestore.');
        print('Para uma solução completa, use o Firebase Admin SDK para excluir o usuário primeiro.');
      }
      // Permitimos continuar, mas avisamos no console
    }
    
    try {
      if (kDebugMode) {
        print('Iniciando criação de usuário: ${user.email}');
      }
      
      // 1. Criar novo documento no Firestore
      final docRef = await _usersCollection.add(user.toFirestore());
      final userId = docRef.id;
      
      // 2. Se foi fornecida uma senha, criar o usuário no Firebase Auth
      String? authUid;
      if (password != null && password.isNotEmpty) {
        try {
          // Criar usuário no Firebase Authentication usando a Cloud Function
          authUid = await _adminAuthService.createUser(
            email: user.email,
            password: password,
            displayName: user.fullName,
          );
          
          if (authUid != null) {
            try {
              // Atualizar o documento com o UID do Auth
              await _usersCollection.doc(userId).update({
                'authUid': authUid,
                'lastModifiedAt': FieldValue.serverTimestamp(),
              });
              
              if (kDebugMode) {
                print('Usuário criado com sucesso no Firebase Authentication: $authUid');
                print('Documento atualizado com o authUid no Firestore');
              }
            } catch (updateError) {
              if (kDebugMode) {
                print('Erro ao atualizar documento com authUid: $updateError');
                print('O usuário foi criado, mas o documento não foi atualizado com o authUid');
              }
            }
          }
        } catch (authError) {
          // Se falhar a criação no Auth, ainda mantemos o registro no Firestore
          if (kDebugMode) {
            print('Erro ao criar usuário no Firebase Auth: $authError');
            print('Usuário foi criado apenas no Firestore');
          }
        }
      }
      
      if (kDebugMode) {
        print('Processo de criação de usuário finalizado com sucesso');
      }
      
      return userId;
    } catch (e) {
      if (kDebugMode) {
        print('Erro ao criar usuário: $e');
      }
      rethrow;
    }
  }
  
  @override
  Future<void> updateUser(SystemUser user) async {
    // Verificar se o email ou username já está em uso por outro usuário
    final emailQuery = await _usersCollection
        .where('email', isEqualTo: user.email)
        .get();
    
    for (var doc in emailQuery.docs) {
      if (doc.id != user.id) {
        throw Exception('Email já está em uso por outro usuário');
      }
    }
    
    final usernameQuery = await _usersCollection
        .where('username', isEqualTo: user.username)
        .get();
    
    for (var doc in usernameQuery.docs) {
      if (doc.id != user.id) {
        throw Exception('Nome de usuário já está em uso por outro usuário');
      }
    }
    
    // Atualizar documento
    await _usersCollection.doc(user.id).update(user.toFirestore());
  }
  
  @override
  Future<void> deleteUser(String id) async {
    try {
      // 1. Obter o documento do usuário para verificar o email e authUid
      final userDoc = await _usersCollection.doc(id).get();
      
      if (!userDoc.exists) {
        if (kDebugMode) {
          print('Documento do usuário não encontrado: $id');
        }
        return;
      }
      
      final userData = userDoc.data();
      final userEmail = userData?['email'] as String?;
      final authUid = userData?['authUid'] as String?;
      
      // 2. Tentar excluir do Firebase Auth
      // Usando a Cloud Function implantada no Firebase
      const bool useCloudFunction = true; // Cloud Function agora está ativa
      
      if (useCloudFunction) {
        // Usando Cloud Function (requer plano Blaze)
        if ((authUid != null && authUid.isNotEmpty) || (userEmail != null && userEmail.isNotEmpty)) {
          try {
            if (kDebugMode) {
              print('Chamando Cloud Function para excluir usuário: ${authUid ?? userEmail}');
            }
            
            final result = await _functions.httpsCallable('deleteUser').call({
              'uid': authUid,
              'email': userEmail,
              'deleteFirestore': false, // Vamos excluir do Firestore manualmente
            });
            
            if (kDebugMode) {
              print('Resultado da exclusão via Cloud Function: ${result.data}');
              print('Usuário excluído com sucesso do Firebase Authentication');
            }
          } catch (functionError) {
            if (kDebugMode) {
              print('Erro ao chamar Cloud Function: $functionError');
              print('Detalhes: ${functionError.toString()}');
              print('Prosseguindo com a exclusão apenas do Firestore.');
            }
            
            // Podemos decidir se queremos lançar uma exceção aqui ou continuar
            // Por enquanto, continuamos com a exclusão do Firestore
          }
        } else {
          if (kDebugMode) {
            print('Nenhum authUid ou email encontrado para excluir do Firebase Auth');
          }
        }
      } 
      // TODO: Implementar fallback para método existente se necessário
      
      // 3. Excluir o documento do Firestore
      await _usersCollection.doc(id).delete();
      
      if (kDebugMode) {
        print('Usuário excluído com sucesso do Firestore: $id');
      }
    } catch (e) {
      if (kDebugMode) {
        print('Erro ao excluir usuário: $e');
      }
      rethrow;
    }
  }
  
  @override
  Future<void> toggleUserStatus(String id, bool isActive) async {
    await _usersCollection.doc(id).update({
      'isActive': isActive,
      'lastModifiedAt': FieldValue.serverTimestamp(),
    });
  }
}