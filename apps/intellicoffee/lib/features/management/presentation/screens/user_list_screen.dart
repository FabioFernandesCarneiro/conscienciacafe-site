import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/management/data/providers/system_user_provider.dart';
import 'package:intellicoffee/features/management/domain/models/system_user.dart';
import 'package:intellicoffee/features/management/presentation/widgets/user_list_item.dart';
import 'package:intellicoffee/shared/widgets/module_header.dart';

class UserListScreen extends ConsumerStatefulWidget {
  const UserListScreen({super.key});

  @override
  ConsumerState<UserListScreen> createState() => _UserListScreenState();
}

class _UserListScreenState extends ConsumerState<UserListScreen> {
  final TextEditingController _searchController = TextEditingController();
  
  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Observa a lista de usuários filtrada
    final usersAsync = ref.watch(filteredUsersProvider);
    // Observa a lista de todos os usuários (para contagem)
    final allUsersAsync = ref.watch(usersProvider);
    // Observa o filtro atual
    final userFilter = ref.watch(userFilterProvider);
    
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: ModuleHeader(
        title: 'Usuários',
        moduleColor: const Color(0xFF4CAF50),  // Cor do módulo de Gestão
        moduleIcon: Icons.people_outlined,
        showBackButton: true,
        backRoute: AppConstants.routeAdminModule,
      ),
      body: Column(
        children: [
          // Barra de pesquisa
          Padding(
            padding: EdgeInsets.all(16.r),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Buscar usuário...',
                prefixIcon: const Icon(Icons.search, color: Colors.grey),
                suffixIcon: Consumer(
                  builder: (context, ref, child) {
                    final searchTerm = ref.watch(userSearchTermProvider);
                    // Mostrar X para limpar a busca se houver um termo
                    return searchTerm.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, color: Colors.grey),
                            onPressed: () {
                              // Limpar campo de busca e provider
                              _searchController.clear();
                              ref.read(userSearchTermProvider.notifier).state = '';
                            },
                          )
                        : const Icon(Icons.search, color: Colors.grey);
                  },
                ),
                filled: true,
                fillColor: Colors.white,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12.r),
                  borderSide: BorderSide.none,
                ),
                contentPadding: EdgeInsets.symmetric(vertical: 0, horizontal: 16.w),
              ),
              onChanged: (value) {
                // Atualizar o termo de busca no provider
                ref.read(userSearchTermProvider.notifier).state = value;
              },
            ),
          ),
          
          // Abas de filtro
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16.w),
            child: Row(
              children: [
                _buildFilterTab(
                  context,
                  'Todos',
                  userFilter == UserFilter.all,
                  () => ref.read(userFilterProvider.notifier).state = UserFilter.all,
                  allUsersAsync.when(
                    data: (users) => users.length,
                    loading: () => 0,
                    error: (_, __) => 0,
                  ),
                ),
                SizedBox(width: 16.w),
                _buildFilterTab(
                  context,
                  'Ativos',
                  userFilter == UserFilter.active,
                  () => ref.read(userFilterProvider.notifier).state = UserFilter.active,
                  allUsersAsync.when(
                    data: (users) => users.where((u) => u.isActive).length,
                    loading: () => 0,
                    error: (_, __) => 0,
                  ),
                ),
                SizedBox(width: 16.w),
                _buildFilterTab(
                  context,
                  'Inativos',
                  userFilter == UserFilter.inactive,
                  () => ref.read(userFilterProvider.notifier).state = UserFilter.inactive,
                  allUsersAsync.when(
                    data: (users) => users.where((u) => !u.isActive).length,
                    loading: () => 0,
                    error: (_, __) => 0,
                  ),
                ),
              ],
            ),
          ),
          
          // Divider
          Divider(
            color: Colors.grey[200],
            height: 1,
            thickness: 1,
          ),
          
          // Lista de usuários
          Expanded(
            child: usersAsync.when(
              data: (users) {
                final searchTerm = ref.watch(userSearchTermProvider);
                
                if (users.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.search_off,
                          size: 64.r,
                          color: Colors.grey[400],
                        ),
                        SizedBox(height: 16.h),
                        Text(
                          searchTerm.isEmpty
                              ? 'Nenhum usuário encontrado'
                              : 'Nenhum resultado para "$searchTerm"',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 16.sp,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        if (searchTerm.isNotEmpty) ...[
                          SizedBox(height: 16.h),
                          ElevatedButton(
                            onPressed: () {
                              _searchController.clear();
                              ref.read(userSearchTermProvider.notifier).state = '';
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.blue[50],
                              foregroundColor: Colors.blue,
                            ),
                            child: const Text('Limpar busca'),
                          ),
                        ],
                      ],
                    ),
                  );
                }
                
                return ListView.separated(
                  padding: EdgeInsets.all(16.r),
                  itemCount: users.length,
                  separatorBuilder: (context, index) => SizedBox(height: 12.h),
                  itemBuilder: (context, index) {
                    final user = users[index];
                    return UserListItem(
                      user: user,
                      onEdit: () {
                        // Navegar para a tela de edição
                        context.go(AppConstants.routeUserDetail.replaceAll(':id', user.id));
                      },
                      onToggleStatus: () {
                        // Ativar/desativar usuário
                        ref.read(usersProvider.notifier).toggleUserStatus(
                          user.id, 
                          !user.isActive,
                        );
                      },
                      onDelete: () {
                        // Confirmar e excluir usuário
                        _showDeleteConfirmationDialog(context, ref, user);
                      },
                    );
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(
                child: Text(
                  'Erro ao carregar usuários: $error',
                  style: TextStyle(
                    color: Colors.red,
                    fontSize: 16.sp,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Navegar para tela de adição de usuário
          context.go(AppConstants.routeUserNew);
        },
        backgroundColor: const Color(0xFF4CAF50),
        child: const Icon(Icons.person_add, color: Colors.white),
      ),
    );
  }
  
  Widget _buildFilterTab(
    BuildContext context,
    String title,
    bool isSelected,
    VoidCallback onTap,
    int count,
  ) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8.r),
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 8.h, horizontal: 12.w),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: isSelected 
                ? const Color(0xFF4CAF50) 
                : Colors.transparent,
              width: 2,
            ),
          ),
        ),
        child: Row(
          children: [
            Text(
              title,
              style: TextStyle(
                color: isSelected ? const Color(0xFF4CAF50) : Colors.grey[600],
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                fontSize: 14.sp,
              ),
            ),
            SizedBox(width: 4.w),
            Container(
              padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 2.h),
              decoration: BoxDecoration(
                color: isSelected ? const Color(0xFF4CAF50) : Colors.grey[300],
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  color: isSelected ? Colors.white : Colors.grey[700],
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _showDeleteConfirmationDialog(
    BuildContext context,
    WidgetRef ref,
    SystemUser user,
  ) async {
    return showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Excluir usuário'),
        content: Text(
          'Você tem certeza que deseja excluir o usuário ${user.fullName}? Esta ação não pode ser desfeita.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('CANCELAR'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              ref.read(usersProvider.notifier).deleteUser(user.id);
            },
            style: TextButton.styleFrom(
              foregroundColor: Colors.red,
            ),
            child: const Text('EXCLUIR'),
          ),
        ],
      ),
    );
  }
}