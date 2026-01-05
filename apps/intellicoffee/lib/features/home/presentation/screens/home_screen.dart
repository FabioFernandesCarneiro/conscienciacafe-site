import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/auth/data/providers/auth_provider.dart';
import 'package:intellicoffee/features/auth/data/providers/user_provider.dart';
import 'package:intellicoffee/features/management/data/providers/user_module_access_provider.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Obtém o usuário atual
    final currentUser = ref.watch(appUserProvider);
    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 16.h),
              child: Row(
                children: [
                  // Logo e nome do app
                  Container(
                    width: 40.r,
                    height: 40.r,
                    decoration: const BoxDecoration(
                      color: Color(0xFFE67E22),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.coffee_outlined,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(width: 12.w),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        AppConstants.appName,
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 18,
                        ),
                      ),
                      Text(
                        'Consciência Café',
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  // Avatar do usuário
                  InkWell(
                    onTap: () {
                      // Mostrar menu popup com as opções do perfil
                      showModalBottomSheet(
                        context: context,
                        backgroundColor: Colors.grey[50],
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.vertical(top: Radius.circular(16.r)),
                        ),
                        builder: (context) => _buildUserProfileMenu(context, ref),
                      );
                    },
                    borderRadius: BorderRadius.circular(20.r),
                    child: Container(
                      width: 40.r,
                      height: 40.r,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.grey[200],
                      ),
                      child: currentUser?.displayName != null
                          ? Center(
                              child: Text(
                                currentUser!.initials,
                                style: TextStyle(
                                  color: Colors.grey[700],
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            )
                          : Icon(
                              Icons.person_outline,
                              color: Colors.grey[700],
                            ),
                    ),
                  ),
                ],
              ),
            ),
            
            // Saudação e mensagem
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 4.h),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Olá, ${currentUser?.displayName?.split(' ').first ?? 'Usuário'}',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  SizedBox(height: 4.h),
                  Text(
                    'O que você precisa fazer hoje?',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[800],
                    ),
                  ),
                ],
              ),
            ),
            
            // Lista de módulos
            Expanded(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 16.h),
                child: Column(
                  children: [
                    // Módulos em grade fixa (sem scroll)
                    Expanded(
                      child: Column(
                        children: [
                          // Primeira linha: Atendimento e Clientes
                          Expanded(
                            child: Row(
                              children: [
                                // Módulo Atendimento
                                Expanded(
                                  child: Consumer(
                                    builder: (context, ref, _) {
                                      final hasAccess = ref.watch(hasModuleAccessProvider('atendimento'));
                                      return _buildMinimalistModuleCard(
                                        context,
                                        title: 'Atendimento',
                                        subtitle: 'Pedidos, mesas e pagamentos',
                                        icon: Icons.store,
                                        color: const Color(0xFFE67E22),
                                        isEnabled: hasAccess,
                                        onTap: () {
                                          // Navegar para o módulo de atendimento
                                          context.go(AppConstants.routeServiceModule);
                                        },
                                      );
                                    },
                                  ),
                                ),
                                SizedBox(width: 14.w),
                                // Módulo Clientes
                                Expanded(
                                  child: Consumer(
                                    builder: (context, ref, _) {
                                      final hasAccess = ref.watch(hasModuleAccessProvider('clientes'));
                                      return _buildMinimalistModuleCard(
                                        context,
                                        title: 'Clientes',
                                        subtitle: 'CRM, fidelidade e marketing',
                                        icon: Icons.people,
                                        color: const Color(0xFF2196F3),
                                        isEnabled: hasAccess,
                                        onTap: () {
                                          // Navegação para o módulo de clientes será implementada
                                        },
                                      );
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ),
                          
                          SizedBox(height: 14.h),
                          
                          // Segunda linha: Torrefação e Vendas B2B
                          Expanded(
                            child: Row(
                              children: [
                                // Módulo Torrefação
                                Expanded(
                                  child: Consumer(
                                    builder: (context, ref, _) {
                                      final hasAccess = ref.watch(hasModuleAccessProvider('torrefacao'));
                                      return _buildMinimalistModuleCard(
                                        context,
                                        title: 'Torrefação',
                                        subtitle: 'Gestão de torras e estoques',
                                        icon: Icons.coffee,
                                        color: const Color(0xFFF57C00),
                                        isEnabled: hasAccess,
                                        onTap: () {
                                          // Navegação será implementada
                                        },
                                      );
                                    },
                                  ),
                                ),
                                SizedBox(width: 14.w),
                                // Módulo Vendas B2B
                                Expanded(
                                  child: Consumer(
                                    builder: (context, ref, _) {
                                      final hasAccess = ref.watch(hasModuleAccessProvider('vendasB2B'));
                                      return _buildMinimalistModuleCard(
                                        context,
                                        title: 'Vendas B2B',
                                        subtitle: 'Clientes corporativos e atacado',
                                        icon: Icons.business,
                                        color: const Color(0xFF3F51B5),
                                        isEnabled: hasAccess,
                                        onTap: () {
                                          // Navegação será implementada
                                        },
                                      );
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ),
                          
                          SizedBox(height: 14.h),
                          
                          // Terceira linha: Eventos e Gestão
                          Expanded(
                            child: Row(
                              children: [
                                // Módulo Eventos
                                Expanded(
                                  child: Consumer(
                                    builder: (context, ref, _) {
                                      final hasAccess = ref.watch(hasModuleAccessProvider('eventos'));
                                      return _buildMinimalistModuleCard(
                                        context,
                                        title: 'Eventos',
                                        subtitle: 'Workshops, cursos e aluguel',
                                        icon: Icons.event,
                                        color: const Color(0xFF9C27B0),
                                        isEnabled: hasAccess,
                                        onTap: () {
                                          // Navegação será implementada
                                        },
                                      );
                                    },
                                  ),
                                ),
                                SizedBox(width: 14.w),
                                // Módulo Gestão
                                Expanded(
                                  child: Consumer(
                                    builder: (context, ref, _) {
                                      final hasAccess = ref.watch(hasModuleAccessProvider('gestao'));
                                      return _buildMinimalistModuleCard(
                                        context,
                                        title: 'Gestão',
                                        subtitle: 'Relatórios, finanças e dashboard',
                                        icon: Icons.insights,
                                        color: const Color(0xFF4CAF50),
                                        isEnabled: hasAccess,
                                        onTap: () {
                                          // Navegar para o módulo de gestão
                                          context.go(AppConstants.routeAdminModule);
                                        },
                                      );
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Menu do perfil do usuário
  Widget _buildUserProfileMenu(BuildContext context, WidgetRef ref) {
    final authService = ref.read(authServiceProvider);
    final user = ref.watch(appUserProvider);
    
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Cabeçalho com informações do usuário
          Padding(
            padding: EdgeInsets.all(16.r),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 24.r,
                  backgroundColor: Colors.grey[200],
                  child: Text(
                    user?.initials ?? 'U',
                    style: TextStyle(
                      fontSize: 20.sp,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey[700],
                    ),
                  ),
                ),
                SizedBox(width: 16.w),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user?.displayName ?? 'Usuário',
                        style: TextStyle(
                          fontSize: 16.sp,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 4.h),
                      Text(
                        user?.email ?? '',
                        style: TextStyle(
                          fontSize: 14.sp,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Divider(),
          
          // Opções do menu
          ListTile(
            leading: Icon(Icons.person_outline, color: Colors.blue[700]),
            title: Text('Meu Perfil'),
            subtitle: Text('Visualizar e editar suas informações'),
            onTap: () {
              // Navegação para perfil (a ser implementada)
              Navigator.pop(context);
              // context.go('/profile'); // Futura implementação
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Perfil será implementado em breve')),
              );
            },
          ),
          ListTile(
            leading: Icon(Icons.lock_outline, color: Colors.orange[700]),
            title: Text('Alterar Senha'),
            subtitle: Text('Atualize sua senha de acesso'),
            onTap: () async {
              Navigator.pop(context);
              // Mostrar diálogo para alteração de senha
              _showChangePasswordDialog(context, ref);
            },
          ),
          ListTile(
            leading: Icon(Icons.settings_outlined, color: Colors.grey[700]),
            title: Text('Configurações'),
            subtitle: Text('Preferências e configurações do app'),
            onTap: () {
              Navigator.pop(context);
              // Navegação para configurações (a ser implementada)
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Configurações serão implementadas em breve')),
              );
            },
          ),
          Divider(),
          ListTile(
            leading: Icon(Icons.exit_to_app, color: Colors.red[700]),
            title: Text('Sair do Aplicativo', style: TextStyle(color: Colors.red[700])),
            onTap: () async {
              // Confirmar antes de sair
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (context) => AlertDialog(
                  title: Text('Confirmar Saída'),
                  content: Text('Tem certeza que deseja sair do aplicativo?'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: Text('Cancelar'),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(context, true),
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.red[700],
                      ),
                      child: Text('Sair'),
                    ),
                  ],
                ),
              );
              
              if (confirmed == true && context.mounted) {
                await authService.signOut();
                
                // Redirecionar para tela de login após logout
                if (context.mounted) {
                  context.go('/login');
                }
              } else if (context.mounted) {
                Navigator.pop(context); // Fechar o menu se cancelou
              }
            },
          ),
          SizedBox(height: 16.h),
        ],
      ),
    );
  }
  
  // Diálogo para alteração de senha
  void _showChangePasswordDialog(BuildContext context, WidgetRef ref) {
    final authService = ref.read(authServiceProvider);
    final currentPasswordController = TextEditingController();
    final newPasswordController = TextEditingController();
    final confirmPasswordController = TextEditingController();
    bool obscureCurrentPassword = true;
    bool obscureNewPassword = true;
    bool obscureConfirmPassword = true;
    
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Text('Alterar Senha'),
          backgroundColor: Colors.grey[50],
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Senha atual
                TextField(
                  controller: currentPasswordController,
                  obscureText: obscureCurrentPassword,
                  decoration: InputDecoration(
                    labelText: 'Senha Atual',
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                    suffixIcon: IconButton(
                      icon: Icon(
                        obscureCurrentPassword ? Icons.visibility_off : Icons.visibility,
                      ),
                      onPressed: () {
                        setState(() {
                          obscureCurrentPassword = !obscureCurrentPassword;
                        });
                      },
                    ),
                  ),
                ),
                SizedBox(height: 16.h),
                
                // Nova senha
                TextField(
                  controller: newPasswordController,
                  obscureText: obscureNewPassword,
                  decoration: InputDecoration(
                    labelText: 'Nova Senha',
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                    suffixIcon: IconButton(
                      icon: Icon(
                        obscureNewPassword ? Icons.visibility_off : Icons.visibility,
                      ),
                      onPressed: () {
                        setState(() {
                          obscureNewPassword = !obscureNewPassword;
                        });
                      },
                    ),
                  ),
                ),
                SizedBox(height: 16.h),
                
                // Confirmar nova senha
                TextField(
                  controller: confirmPasswordController,
                  obscureText: obscureConfirmPassword,
                  decoration: InputDecoration(
                    labelText: 'Confirmar Nova Senha',
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                    suffixIcon: IconButton(
                      icon: Icon(
                        obscureConfirmPassword ? Icons.visibility_off : Icons.visibility,
                      ),
                      onPressed: () {
                        setState(() {
                          obscureConfirmPassword = !obscureConfirmPassword;
                        });
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
          actionsPadding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
          actions: [
            OutlinedButton(
              onPressed: () => Navigator.pop(context),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: Colors.grey[400]!),
                padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8.r),
                ),
              ),
              child: Text(
                'Cancelar',
                style: TextStyle(
                  color: Colors.grey[700],
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            ElevatedButton(
              onPressed: () async {
                // Validar campos
                if (currentPasswordController.text.isEmpty ||
                    newPasswordController.text.isEmpty ||
                    confirmPasswordController.text.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Preencha todos os campos')),
                  );
                  return;
                }
                
                if (newPasswordController.text != confirmPasswordController.text) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('As senhas não coincidem')),
                  );
                  return;
                }
                
                if (newPasswordController.text.length < 6) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('A senha deve ter pelo menos 6 caracteres')),
                  );
                  return;
                }
                
                // Fechar o diálogo e mostrar o carregamento
                Navigator.pop(context);
                
                try {
                  // Reautenticar o usuário antes de alterar a senha
                  final user = FirebaseAuth.instance.currentUser;
                  final email = user?.email;
                  
                  if (user != null && email != null) {
                    // Criar credenciais com senha atual
                    final credential = EmailAuthProvider.credential(
                      email: email,
                      password: currentPasswordController.text,
                    );
                    
                    // Reautenticar
                    await user.reauthenticateWithCredential(credential);
                    
                    // Alterar senha
                    await authService.updatePassword(newPasswordController.text);
                    
                    // Mostrar mensagem de sucesso
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Senha alterada com sucesso'),
                          backgroundColor: Colors.green[700],
                        ),
                      );
                    }
                  }
                } catch (e) {
                  // Mostrar erro
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Erro ao alterar senha: $e'),
                        backgroundColor: Colors.red[700],
                      ),
                    );
                  }
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4CAF50),
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 12.h),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8.r),
                ),
              ),
              child: Text(
                'Alterar',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Novo design minimalista para os módulos
  Widget _buildMinimalistModuleCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
    bool isEnabled = true,
  }) {
    // Cores ajustadas baseadas no estado habilitado/desabilitado
    final cardColor = isEnabled ? Colors.white : Colors.grey[100];
    final iconBgColor = isEnabled ? color.withValues(alpha: 0.15) : Colors.grey[200];
    final iconColor = isEnabled ? color : Colors.grey;
    final titleColor = isEnabled ? Colors.black87 : Colors.grey[600];
    final subtitleColor = isEnabled ? Colors.grey[600] : Colors.grey[400];
    
    return InkWell(
      onTap: isEnabled ? onTap : null, // Desativa o onTap se não estiver habilitado
      borderRadius: BorderRadius.circular(12.r),
      child: Container(
        padding: EdgeInsets.all(16.r),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12.r),
          color: cardColor,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: isEnabled ? 0.05 : 0.02),
              blurRadius: isEnabled ? 8 : 4,
              offset: const Offset(0, 2),
            ),
          ],
          border: isEnabled ? null : Border.all(color: Colors.grey[300]!, width: 1),
        ),
        child: Stack(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Ícone em um círculo colorido
                Container(
                  width: 40.r,
                  height: 40.r,
                  decoration: BoxDecoration(
                    color: iconBgColor,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    icon,
                    color: iconColor,
                    size: 20.sp,
                  ),
                ),
                
                const Spacer(),
                
                // Título
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 13.sp,
                    fontWeight: FontWeight.bold,
                    color: titleColor,
                  ),
                ),
                SizedBox(height: 4.h),
                // Subtítulo
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 10.sp,
                    color: subtitleColor,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                
                const Spacer(),
              ],
            ),
            // Badge de "Acesso negado" para módulos desabilitados
            if (!isEnabled)
              Positioned(
                top: 0,
                right: 0,
                child: Container(
                  padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 2.h),
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(4.r),
                  ),
                  child: Text(
                    'Sem acesso',
                    style: TextStyle(
                      fontSize: 8.sp,
                      color: Colors.grey[700],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}