import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/shared/widgets/app_bottom_navigation.dart';

class ServiceMainScreen extends StatefulWidget {
  const ServiceMainScreen({super.key});

  @override
  State<ServiceMainScreen> createState() => _ServiceMainScreenState();
}

class _ServiceMainScreenState extends State<ServiceMainScreen> {
  int _currentIndex = 0;

  // Definição dos títulos para cada aba
  final List<String> _titles = [
    'Atendimento',
    'Pedidos',
    'Clientes',
    'Relatórios',
  ];

  // Lista de itens do menu de navegação
  final List<BottomNavigationItem> _navigationItems = const [
    BottomNavigationItem(
      icon: Icons.home_outlined,
      activeIcon: Icons.home,
      label: 'Início',
    ),
    BottomNavigationItem(
      icon: Icons.receipt_long_outlined,
      activeIcon: Icons.receipt_long,
      label: 'Pedidos',
    ),
    BottomNavigationItem(
      icon: Icons.people_outline,
      activeIcon: Icons.people,
      label: 'Clientes',
    ),
    BottomNavigationItem(
      icon: Icons.bar_chart_outlined,
      activeIcon: Icons.bar_chart,
      label: 'Relatórios',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Row(
          children: [
            // Logo
            Container(
              width: 36.r,
              height: 36.r,
              decoration: const BoxDecoration(
                color: Color(0xFFE67E22),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.coffee_outlined,
                color: Colors.white,
                size: 20,
              ),
            ),
            SizedBox(width: 12.w),
            // Título
            Text(
              _titles[_currentIndex],
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
          ],
        ),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        actions: [
          // Botão para voltar para a tela de seleção de módulos
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              context.go(AppConstants.routeHome);
            },
          ),
        ],
      ),
      body: _buildCurrentScreen(),
      bottomNavigationBar: AppBottomNavigation(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: _navigationItems,
        activeColor: const Color(0xFFE67E22),
      ),
    );
  }

  // Método para retornar a tela atual com base no índice selecionado
  Widget _buildCurrentScreen() {
    // Para este exemplo, implementaremos apenas a tela inicial (dashboard)
    switch (_currentIndex) {
      case 0:
        return _buildDashboardScreen();
      case 1:
        return const Center(child: Text('Tela de Pedidos'));
      case 2:
        return const Center(child: Text('Tela de Clientes'));
      case 3:
        return const Center(child: Text('Tela de Relatórios'));
      default:
        return _buildDashboardScreen();
    }
  }

  // Tela de dashboard baseada no protótipo
  Widget _buildDashboardScreen() {
    return SingleChildScrollView(
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Saudação e data
            Text(
              'Olá, Carlos!',
              style: TextStyle(
                fontSize: 22.sp,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 4.h),
            Text(
              'Terça-feira, 11 de Maio',
              style: TextStyle(
                fontSize: 14.sp,
                color: Colors.grey[600],
              ),
            ),
            SizedBox(height: 24.h),
            
            // Resumo do dia - HOJE
            Text(
              'HOJE',
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w600,
                color: Colors.grey[600],
                letterSpacing: 1.2,
              ),
            ),
            SizedBox(height: 12.h),
            
            // Cards de estatísticas
            Row(
              children: [
                // Card de Clientes
                Expanded(
                  child: _buildStatCard(
                    icon: Icons.people_outline,
                    iconColor: const Color(0xFF2196F3),
                    iconBackground: const Color(0xFFE3F2FD),
                    title: 'Clientes',
                    value: '12',
                  ),
                ),
                SizedBox(width: 16.w),
                // Card de Pedidos
                Expanded(
                  child: _buildStatCard(
                    icon: Icons.receipt_long_outlined,
                    iconColor: const Color(0xFFE67E22),
                    iconBackground: const Color(0xFFFFF3E0),
                    title: 'Pedidos',
                    value: '18',
                  ),
                ),
              ],
            ),
            SizedBox(height: 24.h),
            
            // Funções Principais
            Text(
              'FUNÇÕES PRINCIPAIS',
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w600,
                color: Colors.grey[600],
                letterSpacing: 1.2,
              ),
            ),
            SizedBox(height: 16.h),
            
            // Grid de funções principais
            Row(
              children: [
                // Novo Atendimento
                Expanded(
                  child: _buildFunctionCard(
                    icon: Icons.add_shopping_cart,
                    iconColor: const Color(0xFFE67E22),
                    iconBackground: const Color(0xFFFFF3E0),
                    title: 'Novo Atendimento',
                    onTap: () {
                      // Navegar para a tela de novo atendimento
                    },
                  ),
                ),
                SizedBox(width: 16.w),
                // Pedidos Ativos
                Expanded(
                  child: _buildFunctionCard(
                    icon: Icons.receipt_outlined,
                    iconColor: const Color(0xFF2196F3),
                    iconBackground: const Color(0xFFE3F2FD),
                    title: 'Pedidos Ativos',
                    onTap: () {
                      // Navegar para a tela de pedidos ativos
                    },
                  ),
                ),
              ],
            ),
            SizedBox(height: 16.h),
            Row(
              children: [
                // Buscar Cliente
                Expanded(
                  child: _buildFunctionCard(
                    icon: Icons.person_search,
                    iconColor: const Color(0xFF9C27B0),
                    iconBackground: const Color(0xFFF3E5F5),
                    title: 'Buscar Cliente',
                    onTap: () {
                      // Navegar para a tela de busca de cliente
                    },
                  ),
                ),
                SizedBox(width: 16.w),
                // Relatório Diário
                Expanded(
                  child: _buildFunctionCard(
                    icon: Icons.insert_chart_outlined,
                    iconColor: const Color(0xFF4CAF50),
                    iconBackground: const Color(0xFFE8F5E9),
                    title: 'Relatório Diário',
                    onTap: () {
                      // Navegar para a tela de relatório diário
                    },
                  ),
                ),
              ],
            ),
            SizedBox(height: 24.h),
            
            // Pedidos Ativos
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'PEDIDOS ATIVOS',
                  style: TextStyle(
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey[600],
                    letterSpacing: 1.2,
                  ),
                ),
                TextButton(
                  onPressed: () {
                    // Ver todos os pedidos ativos
                  },
                  child: Text(
                    'Ver todos',
                    style: TextStyle(
                      color: const Color(0xFFE67E22),
                      fontWeight: FontWeight.w500,
                      fontSize: 14.sp,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 8.h),
            
            // Lista de pedidos ativos
            _buildActiveOrderCard(
              customerName: 'Maria Silva',
              orderItems: 'Cappuccino, Brownie',
              startTime: 'Iniciado às 9:15',
              status: 'Em preparo',
              location: 'Mesa 5',
              isReady: false,
            ),
            SizedBox(height: 12.h),
            _buildActiveOrderCard(
              customerName: 'João Santos',
              orderItems: 'Espresso, Pão de Queijo',
              startTime: 'Iniciado às 9:22',
              status: 'Pronto',
              location: 'Balcão',
              isReady: true,
            ),
          ],
        ),
      ),
    );
  }

  // Card para estatísticas
  Widget _buildStatCard({
    required IconData icon,
    required Color iconColor,
    required Color iconBackground,
    required String title,
    required String value,
  }) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36.r,
                height: 36.r,
                decoration: BoxDecoration(
                  color: iconBackground,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  icon,
                  color: iconColor,
                  size: 20.sp,
                ),
              ),
              SizedBox(width: 8.w),
              Text(
                title,
                style: TextStyle(
                  fontSize: 14.sp,
                  color: Colors.grey[700],
                ),
              ),
            ],
          ),
          SizedBox(height: 12.h),
          Text(
            value,
            style: TextStyle(
              fontSize: 28.sp,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  // Card para funções principais
  Widget _buildFunctionCard({
    required IconData icon,
    required Color iconColor,
    required Color iconBackground,
    required String title,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12.r),
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 20.h),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12.r),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 48.r,
              height: 48.r,
              decoration: BoxDecoration(
                color: iconBackground,
                shape: BoxShape.circle,
              ),
              child: Icon(
                icon,
                color: iconColor,
                size: 24.sp,
              ),
            ),
            SizedBox(height: 12.h),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Card para pedidos ativos
  Widget _buildActiveOrderCard({
    required String customerName,
    required String orderItems,
    required String startTime,
    required String status,
    required String location,
    required bool isReady,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () {
          // Abrir detalhes do pedido
        },
        borderRadius: BorderRadius.circular(12.r),
        child: Padding(
          padding: EdgeInsets.all(16.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Cliente e status
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    customerName,
                    style: TextStyle(
                      fontSize: 16.sp,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Container(
                    padding: EdgeInsets.symmetric(
                      horizontal: 10.w,
                      vertical: 4.h,
                    ),
                    decoration: BoxDecoration(
                      color: isReady
                          ? const Color(0xFFE8F5E9)
                          : const Color(0xFFFFF8E1),
                      borderRadius: BorderRadius.circular(20.r),
                    ),
                    child: Text(
                      status,
                      style: TextStyle(
                        fontSize: 12.sp,
                        color: isReady
                            ? const Color(0xFF4CAF50)
                            : const Color(0xFFFFA000),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 8.h),
              // Itens do pedido
              Text(
                orderItems,
                style: TextStyle(
                  fontSize: 14.sp,
                  color: Colors.grey[700],
                ),
              ),
              SizedBox(height: 8.h),
              // Hora de início e localização
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    startTime,
                    style: TextStyle(
                      fontSize: 12.sp,
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    location,
                    style: TextStyle(
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}