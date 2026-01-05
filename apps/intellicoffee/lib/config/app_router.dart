import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/features/auth/data/providers/auth_provider.dart';
import 'package:intellicoffee/features/auth/presentation/screens/login_screen_improved.dart';
import 'package:intellicoffee/features/auth/presentation/screens/splash_screen.dart';
import 'package:intellicoffee/features/home/presentation/screens/home_screen.dart';
import 'package:intellicoffee/features/management/data/providers/user_module_access_provider.dart';
import 'package:intellicoffee/features/management/presentation/screens/management_home_screen.dart';
import 'package:intellicoffee/features/management/presentation/screens/user_edit_screen_improved.dart';
import 'package:intellicoffee/features/management/presentation/screens/user_list_screen.dart';
import 'package:intellicoffee/features/products/presentation/screens/product_category_form_screen_improved.dart';
import 'package:intellicoffee/features/products/presentation/screens/product_category_list_screen.dart';
import 'package:intellicoffee/features/products/presentation/screens/products_module_screen.dart';
import 'package:intellicoffee/features/service/presentation/screens/service_main_screen.dart';

// Definição das rotas do aplicativo
final _rootNavigatorKey = GlobalKey<NavigatorState>();

// Criamos um Provider para o GoRouter
final routerProvider = Provider<GoRouter>((ref) {
  // Observamos alterações no estado de autenticação
  final authState = ref.watch(authStateProvider);
  final isLoggedIn = authState.when(
    data: (user) => user != null,
    loading: () => false,
    error: (_, __) => false,
  );
  
  // Função auxiliar para verificar acesso ao módulo
  bool hasAccessToModule(String moduleKey) {
    final moduleAccess = ref.read(hasModuleAccessProvider(moduleKey));
    return moduleAccess;
  }

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: AppConstants.routeInitial,
    routes: [
      // Rota inicial - Splash Screen
      GoRoute(
        path: AppConstants.routeInitial,
        builder: (context, state) => const SplashScreen(),
      ),
      
      // Rota de login
      GoRoute(
        path: AppConstants.routeLogin,
        builder: (context, state) => const LoginScreenImproved(),
      ),
      
      // Rota da home - Seletor de módulos
      GoRoute(
        path: AppConstants.routeHome,
        builder: (context, state) => const HomeScreen(),
      ),
      
      // Rota do módulo de atendimento
      GoRoute(
        path: AppConstants.routeServiceModule,
        builder: (context, state) => const ServiceMainScreen(),
        redirect: (context, state) {
          if (!hasAccessToModule('atendimento')) {
            return AppConstants.routeHome; // Redireciona para home se não tiver acesso
          }
          return null; // Permite acesso
        },
      ),
      
      // Rotas do módulo de gestão
      GoRoute(
        path: AppConstants.routeAdminModule,
        builder: (context, state) => const ManagementHomeScreen(),
        redirect: (context, state) {
          if (!hasAccessToModule('gestao')) {
            return AppConstants.routeHome; // Redireciona para home se não tiver acesso
          }
          return null; // Permite acesso
        },
      ),
      GoRoute(
        path: AppConstants.routeUserList,
        builder: (context, state) => const UserListScreen(),
        redirect: (context, state) {
          if (!hasAccessToModule('gestao')) {
            return AppConstants.routeHome; // Redireciona para home se não tiver acesso
          }
          return null; // Permite acesso
        },
      ),
      GoRoute(
        path: AppConstants.routeUserNew,
        builder: (context, state) => const UserEditScreenImproved(),
        redirect: (context, state) {
          if (!hasAccessToModule('gestao')) {
            return AppConstants.routeHome; // Redireciona para home se não tiver acesso
          }
          return null; // Permite acesso
        },
      ),
      GoRoute(
        path: AppConstants.routeUserDetail,
        builder: (context, state) {
          final pathParams = state.uri.pathSegments.length > 2 ? state.uri.pathSegments[2] : '';
          return UserEditScreenImproved(userId: pathParams);
        },
        redirect: (context, state) {
          if (!hasAccessToModule('gestao')) {
            return AppConstants.routeHome; // Redireciona para home se não tiver acesso
          }
          return null; // Permite acesso
        },
      ),
      
      // Rotas do módulo de produtos
      ShellRoute(
        builder: (context, state, child) {
          return ProductsModuleScreen(child: child);
        },
        routes: [
          // Rota principal - produtos
          GoRoute(
            path: AppConstants.routeProductsModule,
            builder: (context, state) => const ProductCategoryListScreen(),
            redirect: (context, state) {
              if (!hasAccessToModule('gestao')) {
                return AppConstants.routeHome;
              }
              return null;
            },
          ),
          
          // Rota de categorias
          GoRoute(
            path: AppConstants.routeProductCategoryList,
            builder: (context, state) => const ProductCategoryListScreen(),
            redirect: (context, state) {
              if (!hasAccessToModule('gestao')) {
                return AppConstants.routeHome;
              }
              return null;
            },
          ),
          
          // Rota de detalhes da categoria
          GoRoute(
            path: AppConstants.routeProductCategoryDetail,
            builder: (context, state) {
              final categoryId = state.pathParameters['id'] ?? '';
              return ProductCategoryFormScreenImproved(categoryId: categoryId);
            },
            redirect: (context, state) {
              if (!hasAccessToModule('gestao')) {
                return AppConstants.routeHome;
              }
              return null;
            },
          ),
          
          // Rota de nova categoria
          GoRoute(
            path: AppConstants.routeProductCategoryNew,
            builder: (context, state) {
              return const ProductCategoryFormScreenImproved();
            },
            redirect: (context, state) {
              if (!hasAccessToModule('gestao')) {
                return AppConstants.routeHome;
              }
              return null;
            },
          ),
          
          // Rota de personalizações
          GoRoute(
            path: AppConstants.routeProductCustomizationList,
            builder: (context, state) {
              // TODO: Implementar tela de listagem de personalizações
              return const ProductCategoryListScreen();
            },
            redirect: (context, state) {
              if (!hasAccessToModule('gestao')) {
                return AppConstants.routeHome;
              }
              return null;
            },
          ),
        ],
      ),
    ],
    
    // Redirecionar com base no estado de autenticação
    redirect: (context, state) {
      // Rotas públicas (acessíveis sem login)
      final isInitialRoute = state.uri.path == AppConstants.routeInitial;
      final isLoginRoute = state.uri.path == AppConstants.routeLogin;
      
      // Lógica de redirecionamento
      // Se estamos em uma rota pública, não redirecionamos
      if (isInitialRoute) return null;
      
      // Se o usuário não está logado e não está na tela de login, redireciona para o login
      if (!isLoggedIn && !isLoginRoute) {
        return AppConstants.routeLogin;
      }
      
      // Se o usuário está logado e está na tela de login, redireciona para a home
      if (isLoggedIn && isLoginRoute) {
        return AppConstants.routeHome;
      }
      
      // Permite acessar a rota solicitada (sem redirecionamento)
      return null;
    },
    
    // Página de erro para rotas não encontradas
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Página não encontrada')),
      body: Center(
        child: Text('Erro: ${state.uri.toString()} não existe'),
      ),
    ),
  );
});
