import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/auth/data/providers/user_provider.dart';
import 'package:intellicoffee/shared/widgets/app_bottom_navigation.dart';
import 'package:intellicoffee/shared/widgets/module_header.dart';

class ManagementHomeScreen extends ConsumerStatefulWidget {
  const ManagementHomeScreen({super.key});

  @override
  ConsumerState<ManagementHomeScreen> createState() => _ManagementHomeScreenState();
}

class _ManagementHomeScreenState extends ConsumerState<ManagementHomeScreen> {
  int _currentIndex = 0;
  
  // Lista de itens do menu de navegação
  final List<BottomNavigationItem> _navigationItems = const [
    BottomNavigationItem(
      icon: Icons.home_outlined,
      activeIcon: Icons.home,
      label: 'Início',
    ),
    BottomNavigationItem(
      icon: Icons.bar_chart_outlined,
      activeIcon: Icons.bar_chart,
      label: 'Relatórios',
    ),
    BottomNavigationItem(
      icon: Icons.account_balance_wallet_outlined,
      activeIcon: Icons.account_balance_wallet,
      label: 'Financeiro',
    ),
    BottomNavigationItem(
      icon: Icons.settings_outlined,
      activeIcon: Icons.settings,
      label: 'Config',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    // Obtém o usuário atual
    final currentUser = ref.watch(appUserProvider);
    final theme = Theme.of(context);
    
    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      appBar: const ModuleHeader(
        title: 'Gestão',
        moduleColor: Color(0xFF4CAF50),
        moduleIcon: Icons.insights,
      ),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            
            // Greeting and Date
            _buildGreeting(currentUser?.displayName),
            
            // Dashboard section
            _buildDashboard(),
            
            // Configurations section
            _buildConfigurationsSection(context),
          ],
        ),
      ),
      bottomNavigationBar: AppBottomNavigation(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: _navigationItems,
        activeColor: theme.colorScheme.primary,
      ),
    );
  }
  
  
  Widget _buildGreeting(String? userName) {
    // Get current date
    final now = DateTime.now();
    final weekday = _getWeekdayName(now.weekday);
    final day = now.day;
    final month = _getMonthName(now.month);
    final theme = Theme.of(context);
    
    // Extract first name if available
    final firstName = userName?.split(' ').first ?? 'Usuário';
    
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Olá, $firstName!',
            style: theme.textTheme.titleLarge,
          ),
          SizedBox(height: 4.h),
          Text(
            '$weekday, $day de $month',
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
  
  Widget _buildDashboard() {
    final theme = Theme.of(context);
    
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 16.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'DASHBOARD',
            style: TextStyle(
              fontSize: 12.sp,
              fontWeight: FontWeight.w500,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              letterSpacing: 1.2,
            ),
          ),
          SizedBox(height: 16.h),
          Row(
            children: [
              // Revenue card
              Expanded(
                child: _buildMetricCard(
                  title: 'Faturamento',
                  value: 'R\$ 3.450',
                  change: '+12% vs semana anterior',
                  isPositive: true,
                  icon: Icons.attach_money,
                  color: theme.colorScheme.secondary.withValues(alpha: 0.1),
                  iconColor: theme.colorScheme.secondary,
                ),
              ),
              SizedBox(width: 16.w),
              // Sales card
              Expanded(
                child: _buildMetricCard(
                  title: 'Vendas',
                  value: '126',
                  change: '+8% vs semana anterior',
                  isPositive: true,
                  icon: Icons.show_chart,
                  color: theme.colorScheme.primary.withValues(alpha: 0.1),
                  iconColor: theme.colorScheme.primary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildConfigurationsSection(BuildContext context) {
    final theme = Theme.of(context);
    
    return Expanded(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'CONFIGURAÇÕES',
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: FontWeight.w500,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                letterSpacing: 1.2,
              ),
            ),
            SizedBox(height: 16.h),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                mainAxisSpacing: 16.h,
                crossAxisSpacing: 16.w,
                childAspectRatio: 1.5,
                physics: const BouncingScrollPhysics(),
                children: [
                  // Produtos (highlighted)
                  _buildConfigCardWithTap(
                    context,
                    title: 'Produtos',
                    subtitle: 'Cadastro e gestão',
                    icon: Icons.inventory_2_outlined,
                    color: theme.colorScheme.primary.withValues(alpha: 0.1),
                    iconColor: theme.colorScheme.primary,
                    onTap: () => context.go(AppConstants.routeProductsModule),
                    isHighlighted: true,
                    highlightText: 'Atualizado frequentemente',
                  ),
                  
                  // Usuários
                  _buildConfigCardWithTap(
                    context,
                    title: 'Usuários',
                    subtitle: 'Acesso por módulos',
                    icon: Icons.people_outline,
                    color: theme.colorScheme.secondary.withValues(alpha: 0.1),
                    iconColor: theme.colorScheme.secondary,
                    onTap: () => context.go(AppConstants.routeUserList),
                  ),
                  
                  // Áreas
                  _buildConfigCardWithTap(
                    context,
                    title: 'Áreas',
                    subtitle: 'Centros de custo e ambientes',
                    icon: Icons.grid_view_outlined,
                    color: Colors.purple[50]!,
                    iconColor: Colors.purple,
                    onTap: () {},
                  ),
                  
                  // Horários
                  _buildConfigCardWithTap(
                    context,
                    title: 'Horários',
                    subtitle: 'Funcionamento e turnos',
                    icon: Icons.access_time_outlined,
                    color: Colors.amber[50]!,
                    iconColor: Colors.amber,
                    onTap: () {},
                  ),
                  
                  // Dados Fiscais
                  _buildConfigCardWithTap(
                    context,
                    title: 'Dados Fiscais',
                    subtitle: 'Emissão de NF e cupons',
                    icon: Icons.description_outlined,
                    color: Colors.blue[50]!,
                    iconColor: Colors.blue,
                    onTap: () {},
                  ),
                  
                  // Pagamentos
                  _buildConfigCardWithTap(
                    context,
                    title: 'Pagamentos',
                    subtitle: 'Formas de pagamento',
                    icon: Icons.credit_card_outlined,
                    color: Colors.red[50]!,
                    iconColor: Colors.red,
                    onTap: () {},
                  ),
                  
                  // Fornecedores
                  _buildConfigCardWithTap(
                    context,
                    title: 'Fornecedores',
                    subtitle: 'Cadastro e contatos',
                    icon: Icons.business_outlined, 
                    color: Colors.teal[50]!,
                    iconColor: Colors.teal,
                    onTap: () {},
                  ),
                  
                  // Impressoras
                  _buildConfigCardWithTap(
                    context,
                    title: 'Impressoras',
                    subtitle: 'Configuração e rotas',
                    icon: Icons.print_outlined,
                    color: Colors.grey[200]!,
                    iconColor: Colors.grey[700]!,
                    onTap: () {},
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildMetricCard({
    required String title,
    required String value,
    required String change,
    required bool isPositive,
    required IconData icon,
    required Color color,
    required Color iconColor,
  }) {
    final theme = Theme.of(context);
    
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8.r),
        border: Border.all(color: theme.colorScheme.outline.withValues(alpha: 0.5)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon and title
          Row(
            children: [
              Container(
                width: 30.r,
                height: 30.r,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  icon,
                  color: iconColor,
                  size: 16.sp,
                ),
              ),
              SizedBox(width: 8.w),
              Text(
                title,
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ),
          SizedBox(height: 12.h),
          // Value
          Text(
            value,
            style: theme.textTheme.headlineMedium,
          ),
          SizedBox(height: 4.h),
          // Change
          Text(
            change,
            style: TextStyle(
              fontSize: 12.sp,
              color: isPositive ? theme.colorScheme.primary : theme.colorScheme.error,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildConfigCardWithTap(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required Color iconColor,
    required VoidCallback onTap,
    bool isHighlighted = false,
    String highlightText = '',
  }) {
    final theme = Theme.of(context);
    
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8.r),
      child: Container(
        padding: EdgeInsets.all(12.r),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8.r),
          border: isHighlighted 
            ? Border.all(color: theme.colorScheme.primary, width: 1.5)
            : Border.all(color: theme.colorScheme.outline.withValues(alpha: 0.5)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.03),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Icon
            Container(
              width: 32.r,
              height: 32.r,
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
              ),
              child: Icon(
                icon,
                color: iconColor,
                size: 18.sp,
              ),
            ),
            const Spacer(),
            // Title
            Text(
              title,
              style: theme.textTheme.titleMedium,
            ),
            SizedBox(height: 2.h),
            // Subtitle
            Text(
              subtitle,
              style: theme.textTheme.bodySmall,
            ),
            // Highlight text if applicable
            if (isHighlighted) ...[
              SizedBox(height: 4.h),
              Text(
                highlightText,
                style: TextStyle(
                  fontSize: 10.sp,
                  color: theme.colorScheme.primary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
  
  
  // Helper methods
  String _getWeekdayName(int weekday) {
    switch (weekday) {
      case 1: return 'Segunda-feira';
      case 2: return 'Terça-feira';
      case 3: return 'Quarta-feira';
      case 4: return 'Quinta-feira';
      case 5: return 'Sexta-feira';
      case 6: return 'Sábado';
      case 7: return 'Domingo';
      default: return '';
    }
  }
  
  String _getMonthName(int month) {
    switch (month) {
      case 1: return 'Janeiro';
      case 2: return 'Fevereiro';
      case 3: return 'Março';
      case 4: return 'Abril';
      case 5: return 'Maio';
      case 6: return 'Junho';
      case 7: return 'Julho';
      case 8: return 'Agosto';
      case 9: return 'Setembro';
      case 10: return 'Outubro';
      case 11: return 'Novembro';
      case 12: return 'Dezembro';
      default: return '';
    }
  }
}