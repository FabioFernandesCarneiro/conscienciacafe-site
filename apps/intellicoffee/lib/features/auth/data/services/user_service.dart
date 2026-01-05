import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/auth/domain/models/app_user.dart';

class UserService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  // Referência para a coleção de usuários
  CollectionReference get _usersCollection => 
      _firestore.collection(AppConstants.colUsers);

  // Obter dados do usuário do Firestore
  Future<Map<String, dynamic>?> getUserData(String uid) async {
    try {
      DocumentSnapshot doc = await _usersCollection.doc(uid).get();
      return doc.exists ? doc.data() as Map<String, dynamic> : null;
    } catch (e) {
      if (kDebugMode) {
        print('Error getting user data: $e');
      }
      return null;
    }
  }

  // Atualizar ou criar dados do usuário
  Future<void> updateUserData(AppUser user) async {
    try {
      await _usersCollection.doc(user.uid).set({
        'email': user.email,
        'displayName': user.displayName,
        'photoURL': user.photoURL,
        'isEmailVerified': user.isEmailVerified,
        'lastLogin': FieldValue.serverTimestamp(),
        'updatedAt': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));
    } catch (e) {
      if (kDebugMode) {
        print('Error updating user data: $e');
      }
      rethrow;
    }
  }

  // Criar um novo usuário no Firestore após registro
  Future<void> createUserRecord(User user) async {
    try {
      await _usersCollection.doc(user.uid).set({
        'uid': user.uid,
        'email': user.email,
        'displayName': user.displayName,
        'photoURL': user.photoURL,
        'isEmailVerified': user.emailVerified,
        'createdAt': FieldValue.serverTimestamp(),
        'updatedAt': FieldValue.serverTimestamp(),
        'lastLogin': FieldValue.serverTimestamp(),
        'role': 'user', // Papel padrão
        'isActive': true,
      });
    } catch (e) {
      if (kDebugMode) {
        print('Error creating user record: $e');
      }
      rethrow;
    }
  }

  // Atualizar último login
  Future<void> updateLastLogin(String uid) async {
    try {
      // Verificar se o usuário existe
      bool userExists = await this.userExists(uid);

      if (userExists) {
        // Se o documento existe, apenas atualiza o lastLogin
        await _usersCollection.doc(uid).update({
          'lastLogin': FieldValue.serverTimestamp(),
        });
      } else {
        // Se o documento não existe, cria um novo com dados básicos
        User? authUser = _auth.currentUser;
        if (authUser != null) {
          await createUserRecord(authUser);
        } else {
          // Fallback caso o currentUser não esteja disponível
          await _usersCollection.doc(uid).set({
            'uid': uid,
            'createdAt': FieldValue.serverTimestamp(),
            'updatedAt': FieldValue.serverTimestamp(),
            'lastLogin': FieldValue.serverTimestamp(),
            'role': 'user',
            'isActive': true,
          });
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('Error updating last login: $e');
      }
      // Não propagamos o erro, pois isso não deve interromper o fluxo de login
    }
  }

  // Verificar se o usuário existe no Firestore
  Future<bool> userExists(String uid) async {
    try {
      DocumentSnapshot doc = await _usersCollection.doc(uid).get();
      return doc.exists;
    } catch (e) {
      if (kDebugMode) {
        print('Error checking if user exists: $e');
      }
      return false;
    }
  }

  // Atualizar dados do perfil
  Future<void> updateProfile({
    required String uid,
    String? displayName,
    String? photoURL,
  }) async {
    try {
      // Atualizar no Auth
      if (displayName != null || photoURL != null) {
        await _auth.currentUser?.updateDisplayName(displayName);
        await _auth.currentUser?.updatePhotoURL(photoURL);
      }

      // Atualizar no Firestore
      final updateData = <String, dynamic>{
        'updatedAt': FieldValue.serverTimestamp(),
      };

      if (displayName != null) {
        updateData['displayName'] = displayName;
      }

      if (photoURL != null) {
        updateData['photoURL'] = photoURL;
      }

      await _usersCollection.doc(uid).update(updateData);
    } catch (e) {
      if (kDebugMode) {
        print('Error updating profile: $e');
      }
      rethrow;
    }
  }
}