import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/auth/data/providers/auth_provider.dart';

/// Widget que monitora o estado de sessão e mostra um alerta quando a sessão é perdida
class SessionLostMonitor extends ConsumerWidget {
  final Widget child;
  
  const SessionLostMonitor({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Monitorar o estado de sessão perdida
    final sessionLost = ref.watch(sessionLostNotifierProvider);
    
    // Se a sessão foi perdida, mostrar um diálogo
    if (sessionLost) {
      // Usar addPostFrameCallback para evitar chamar setState durante o build
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _showSessionLostDialog(context, ref);
      });
    }
    
    return child;
  }
  
  /// Mostra o diálogo de sessão perdida
  void _showSessionLostDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Sessão encerrada'),
        content: const Text(
          'Sua sessão foi encerrada durante a criação do novo usuário. '
          'É necessário fazer login novamente para continuar usando o aplicativo.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              // Resetar a notificação
              ref.read(sessionLostNotifierProvider.notifier).resetNotification();
              // Navegar para a tela de login
              context.go(AppConstants.routeLogin);
            },
            child: const Text('FAZER LOGIN'),
          ),
        ],
      ),
    );
  }
} 