import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intellicoffee/features/management/domain/models/system_user.dart';

class UserListItem extends StatelessWidget {
  final SystemUser user;
  final VoidCallback onEdit;
  final VoidCallback onToggleStatus;
  final VoidCallback onDelete;

  const UserListItem({
    super.key,
    required this.user,
    required this.onEdit,
    required this.onToggleStatus,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    // Definir opacidade com base no status do usuário
    final opacity = user.isActive ? 1.0 : 0.6;
    
    return Opacity(
      opacity: opacity,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12.r),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Padding(
          padding: EdgeInsets.all(16.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Nome, função e ações
              Row(
                children: [
                  // Avatar
                  Container(
                    width: 40.r,
                    height: 40.r,
                    decoration: BoxDecoration(
                      color: _getAvatarColor(user.role),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Text(
                        user.initials,
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 16.sp,
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 12.w),
                  
                  // Nome e função
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user.fullName,
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16.sp,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                        SizedBox(height: 2.h),
                        Row(
                          children: [
                            Container(
                              padding: EdgeInsets.symmetric(
                                horizontal: 6.w,
                                vertical: 2.h,
                              ),
                              decoration: BoxDecoration(
                                color: _getRoleChipColor(user.role).withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(4.r),
                              ),
                              child: Text(
                                user.role.displayName,
                                style: TextStyle(
                                  color: _getRoleChipColor(user.role),
                                  fontSize: 12.sp,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  
                  // Actions
                  Row(
                    children: [
                      // Edit button
                      IconButton(
                        icon: Icon(
                          Icons.edit_outlined,
                          color: Colors.grey[700],
                          size: 20.r,
                        ),
                        visualDensity: VisualDensity.compact,
                        onPressed: onEdit,
                      ),
                      // Toggle status button
                      IconButton(
                        icon: Icon(
                          user.isActive
                              ? Icons.person_off_outlined
                              : Icons.person_outlined,
                          color: user.isActive ? Colors.orange : Colors.green,
                          size: 20.r,
                        ),
                        visualDensity: VisualDensity.compact,
                        onPressed: onToggleStatus,
                      ),
                      // Delete button
                      IconButton(
                        icon: Icon(
                          Icons.delete_outline,
                          color: Colors.red[400],
                          size: 20.r,
                        ),
                        visualDensity: VisualDensity.compact,
                        onPressed: onDelete,
                      ),
                    ],
                  ),
                ],
              ),
              
              // Email
              Padding(
                padding: EdgeInsets.only(left: 52.w, top: 4.h),
                child: Text(
                  user.email,
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 14.sp,
                  ),
                ),
              ),
              
              // Divider
              Padding(
                padding: EdgeInsets.symmetric(vertical: 12.h),
                child: Divider(
                  color: Colors.grey[200],
                  height: 1,
                ),
              ),
              
              // Módulos de acesso
              Padding(
                padding: EdgeInsets.only(left: 52.w),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Acesso aos módulos:',
                      style: TextStyle(
                        color: Colors.grey[700],
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    SizedBox(height: 8.h),
                    Wrap(
                      spacing: 6.w,
                      runSpacing: 6.h,
                      children: _buildModuleChips(),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  // Obter a cor para o avatar com base na função
  Color _getAvatarColor(UserRole role) {
    return Color(role.color);
  }
  
  // Obter a cor para o chip de função
  Color _getRoleChipColor(UserRole role) {
    return Color(role.color);
  }
  
  // Construir os chips para cada módulo
  List<Widget> _buildModuleChips() {
    final modules = <MapEntry<String, Color>>[
      if (user.moduleAccess['atendimento'] == true)
        const MapEntry('Atendimento', Color(0xFFE67E22)),
      if (user.moduleAccess['clientes'] == true)
        const MapEntry('Clientes', Color(0xFF2196F3)),
      if (user.moduleAccess['torrefacao'] == true)
        const MapEntry('Torrefação', Color(0xFFF57C00)),
      if (user.moduleAccess['vendasB2B'] == true)
        const MapEntry('Vendas B2B', Color(0xFF3F51B5)),
      if (user.moduleAccess['eventos'] == true)
        const MapEntry('Eventos', Color(0xFF9C27B0)),
      if (user.moduleAccess['gestao'] == true)
        const MapEntry('Gestão', Color(0xFF4CAF50)),
    ];
    
    return modules.map((entry) {
      return Container(
        padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
        decoration: BoxDecoration(
          color: entry.value.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(
            color: entry.value.withValues(alpha: 0.3),
            width: 1,
          ),
        ),
        child: Text(
          entry.key,
          style: TextStyle(
            color: entry.value,
            fontSize: 12.sp,
            fontWeight: FontWeight.w500,
          ),
        ),
      );
    }).toList();
  }
}