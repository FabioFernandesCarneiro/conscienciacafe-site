import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/foundation.dart';

/// Serviço para gerenciar uploads de fotos de usuários
class UserPhotoService {
  final FirebaseStorage _storage;
  
  UserPhotoService({FirebaseStorage? storage}) 
      : _storage = storage ?? FirebaseStorage.instance;
  
  /// Faz upload de uma foto de usuário para o Firebase Storage
  Future<String?> uploadUserPhoto(String userId, Uint8List imageData) async {
    try {
      // Referência para o arquivo no Storage
      final storageRef = _storage
          .ref()
          .child('user_photos')
          .child('$userId.jpg');

      // Metadados (importante para web)
      final metadata = SettableMetadata(
        contentType: 'image/jpeg',
        customMetadata: {'picked-file-path': 'user_photo'},
      );

      // Upload do arquivo
      final uploadTask = storageRef.putData(imageData, metadata);
      
      // Aguardar conclusão do upload
      final snapshot = await uploadTask.whenComplete(() {});
      
      // Obter URL do arquivo
      final downloadUrl = await snapshot.ref.getDownloadURL();
      return downloadUrl;
    } catch (e) {
      debugPrint('Erro ao fazer upload da foto: $e');
      return null;
    }
  }
  
  /// Exclui uma foto de usuário do Firebase Storage
  Future<bool> deleteUserPhoto(String userId) async {
    try {
      final storageRef = _storage
          .ref()
          .child('user_photos')
          .child('$userId.jpg');
      
      await storageRef.delete();
      return true;
    } catch (e) {
      debugPrint('Erro ao excluir foto: $e');
      return false;
    }
  }
}