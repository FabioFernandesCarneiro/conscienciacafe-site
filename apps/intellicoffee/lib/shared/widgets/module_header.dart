import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';

/// Widget reutilizável para o cabeçalho dos módulos
class ModuleHeader extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final Color moduleColor;
  final IconData moduleIcon;
  final bool showBackButton;
  final String? backRoute;
  
  const ModuleHeader({
    super.key,
    required this.title,
    required this.moduleColor,
    required this.moduleIcon,
    this.showBackButton = false,
    this.backRoute,
  });
  
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return AppBar(
      title: Row(
        children: [
          // Logo do módulo
          Container(
            width: 36.r,
            height: 36.r,
            decoration: BoxDecoration(
              color: moduleColor,
              shape: BoxShape.circle,
            ),
            child: Icon(
              moduleIcon,
              color: Colors.white,
              size: 20.sp,
            ),
          ),
          SizedBox(width: 12.w),
          // Título do módulo
          Text(
            title,
            style: theme.textTheme.titleLarge,
          ),
        ],
      ),
      backgroundColor: theme.colorScheme.surface,
      foregroundColor: theme.colorScheme.onSurface,
      elevation: 0,
      // Se showBackButton for true, mostrar botão voltar
      // Caso contrário, mostrar botão para voltar à home principal
      leading: showBackButton
          ? IconButton(
              icon: Icon(Icons.arrow_back, color: theme.colorScheme.onSurface),
              onPressed: () {
                if (backRoute != null) {
                  context.go(backRoute!);
                } else {
                  Navigator.of(context).pop();
                }
              },
            )
          : null,
      actions: [
        // Botão para voltar para a tela de seleção de módulos
        IconButton(
          icon: Icon(Icons.logout, color: theme.colorScheme.onSurface),
          onPressed: () {
            context.go(AppConstants.routeHome);
          },
        ),
      ],
    );
  }
  
  @override
  Size get preferredSize => Size.fromHeight(kToolbarHeight);
}