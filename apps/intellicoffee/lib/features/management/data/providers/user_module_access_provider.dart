import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intellicoffee/features/auth/data/providers/user_provider.dart';

/// Mapeamento de chaves de módulos para nomes legíveis
const Map<String, String> moduleKeys = {
  'atendimento': 'Atendimento',
  'clientes': 'Clientes',
  'torrefacao': 'Torrefação',
  'vendasB2B': 'Vendas B2B',
  'eventos': 'Eventos',
  'gestao': 'Gestão',
};

/// Provider para acessar as permissões de módulos do usuário atual
final userModuleAccessProvider = FutureProvider<Map<String, bool>>((ref) async {
  final userId = ref.watch(userIdProvider);
  
  // Se não houver usuário logado, retorna mapa vazio
  if (userId == null) {
    return {};
  }
  
  // Para admins, concede acesso a todos os módulos automaticamente
  final isAdmin = ref.watch(isAdminProvider);
  if (isAdmin) {
    return {
      'atendimento': true,
      'clientes': true,
      'torrefacao': true,
      'vendasB2B': true,
      'eventos': true,
      'gestao': true,
    };
  }
  
  // Busca as permissões do usuário no Firestore
  try {
    final userDoc = await FirebaseFirestore.instance
        .collection('users')
        .doc(userId)
        .get();
    
    if (!userDoc.exists || !userDoc.data()!.containsKey('moduleAccess')) {
      // Por padrão, se não tiver configuração, concede acesso apenas ao atendimento
      return {
        'atendimento': true,
        'clientes': false,
        'torrefacao': false,
        'vendasB2B': false,
        'eventos': false,
        'gestao': false,
      };
    }
    
    // Converte o campo 'moduleAccess' de Map<String, dynamic> para Map<String, bool>
    final Map<String, dynamic> accessData = userDoc.data()!['moduleAccess'] ?? {};
    final Map<String, bool> moduleAccess = {};
    
    // Processa cada módulo e garante que todos os módulos estejam presentes
    for (var key in moduleKeys.keys) {
      moduleAccess[key] = accessData[key] as bool? ?? false;
    }
    
    return moduleAccess;
  } catch (e) {
    // Em caso de erro, retorna permissões padrão
    return {
      'atendimento': true,
      'clientes': false,
      'torrefacao': false,
      'vendasB2B': false,
      'eventos': false,
      'gestao': false,
    };
  }
});

/// Provider simplificado para verificar acesso a um módulo específico
final hasModuleAccessProvider = Provider.family<bool, String>((ref, moduleKey) {
  final moduleAccessAsyncValue = ref.watch(userModuleAccessProvider);
  
  return moduleAccessAsyncValue.when(
    data: (moduleAccess) => moduleAccess[moduleKey] ?? false,
    loading: () => false, // Durante o carregamento, nega acesso por segurança
    error: (_, __) => false, // Em caso de erro, nega acesso por segurança
  );
});