import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:intellicoffee/features/auth/data/services/user_service.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final UserService _userService = UserService();

  // Obter usuário atual
  User? get currentUser => _auth.currentUser;

  // Stream de alterações do estado de autenticação
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  // Login com email e senha
  Future<UserCredential> signInWithEmailAndPassword({
    required String email,
    required String password,
  }) async {
    try {
      UserCredential result = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      // Atualizar último login no Firestore
      if (result.user != null) {
        await _userService.updateLastLogin(result.user!.uid);
      }
      
      return result;
    } on FirebaseAuthException catch (e) {
      if (kDebugMode) {
        debugPrint('Error signing in: ${e.message}');
      }
      rethrow;
    }
  }

  // Cadastro com email e senha
  Future<UserCredential> createUserWithEmailAndPassword({
    required String email,
    required String password,
    String? displayName,
  }) async {
    try {
      // Criar usuário no Firebase Auth
      UserCredential result = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      
      // Atualizar nome de exibição se fornecido
      if (displayName != null && result.user != null) {
        await result.user!.updateDisplayName(displayName);
      }
      
      // Criar registro do usuário no Firestore
      if (result.user != null) {
        // Recarregar usuário para obter os dados atualizados
        await result.user!.reload();
        await _userService.createUserRecord(result.user!);
      }
      
      return result;
    } on FirebaseAuthException catch (e) {
      if (kDebugMode) {
        debugPrint('Error creating user: ${e.message}');
      }
      rethrow;
    }
  }

  // Logout
  Future<void> signOut() async {
    await _auth.signOut();
  }

  // Recuperação de senha
  Future<void> sendPasswordResetEmail({required String email}) async {
    try {
      await _auth.sendPasswordResetEmail(email: email);
    } on FirebaseAuthException catch (e) {
      if (kDebugMode) {
        debugPrint('Error sending password reset email: ${e.message}');
      }
      rethrow;
    }
  }

  // Verificar se o usuário está logado
  bool isUserLoggedIn() {
    return currentUser != null;
  }

  // Obter o ID do usuário atual
  String? getCurrentUserId() {
    return currentUser?.uid;
  }

  // Obter o email do usuário atual
  String? getCurrentUserEmail() {
    return currentUser?.email;
  }
  
  // Atualizar dados do perfil
  Future<void> updateProfile({
    String? displayName,
    String? photoURL,
  }) async {
    try {
      final user = currentUser;
      if (user == null) throw Exception('Nenhum usuário logado');
      
      // Atualizar no Firebase Auth
      if (displayName != null) {
        await user.updateDisplayName(displayName);
      }
      
      if (photoURL != null) {
        await user.updatePhotoURL(photoURL);
      }
      
      // Atualizar no Firestore
      await _userService.updateProfile(
        uid: user.uid,
        displayName: displayName,
        photoURL: photoURL,
      );
      
      // Recarregar usuário para obter os dados atualizados
      await user.reload();
    } catch (e) {
      if (kDebugMode) {
        debugPrint('Error updating profile: $e');
      }
      rethrow;
    }
  }
  
  // Atualizar email
  Future<void> updateEmail(String newEmail) async {
    try {
      final user = currentUser;
      if (user == null) throw Exception('Nenhum usuário logado');
      
      // Usar verifyBeforeUpdateEmail em vez de updateEmail (deprecated)
      // Isso enviará um email de verificação antes de atualizar
      await user.verifyBeforeUpdateEmail(newEmail);
      
      // Nota: O email só será atualizado após o usuário verificar o link no email
      if (kDebugMode) {
        debugPrint('Email de verificação enviado para: $newEmail');
      }
    } on FirebaseAuthException catch (e) {
      if (kDebugMode) {
        debugPrint('Error updating email: ${e.message}');
      }
      rethrow;
    }
  }
  
  // Atualizar senha
  Future<void> updatePassword(String newPassword) async {
    try {
      final user = currentUser;
      if (user == null) throw Exception('Nenhum usuário logado');
      
      await user.updatePassword(newPassword);
    } on FirebaseAuthException catch (e) {
      if (kDebugMode) {
        debugPrint('Error updating password: ${e.message}');
      }
      rethrow;
    }
  }

  // Alterar senha com reautenticação
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    try {
      final user = currentUser;
      if (user == null) throw Exception('Nenhum usuário logado');
      
      // Reautenticar usuário com senha atual
      final credential = EmailAuthProvider.credential(
        email: user.email!,
        password: currentPassword,
      );
      
      await user.reauthenticateWithCredential(credential);
      
      // Atualizar para nova senha
      await user.updatePassword(newPassword);
    } on FirebaseAuthException catch (e) {
      if (kDebugMode) {
        debugPrint('Error changing password: ${e.message}');
      }
      rethrow;
    }
  }
}