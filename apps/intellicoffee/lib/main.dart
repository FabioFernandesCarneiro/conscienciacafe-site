import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intellicoffee/config/app_router.dart';
import 'package:intellicoffee/firebase_options.dart'; // Usando o arquivo gerado pelo FlutterFire na raiz do lib
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/core/theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar Firebase
  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
    
    // Nota: A configuração antiga setRootPathForWeb foi removida
    // nas versões mais recentes do Firebase Storage, pois não é mais necessária
    
    if (kDebugMode) {
      print('Firebase inicializado com sucesso');
    }
  } catch (e) {
    if (kDebugMode) {
      print('Erro ao inicializar Firebase: $e');
    }
    throw Exception('Falha ao inicializar Firebase. O aplicativo requer o Firebase para funcionar.');
  }

  runApp(
    const ProviderScope(
      child: MyApp(),
    ),
  );
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Usa o router provider
    final router = ref.watch(routerProvider);
    
    return ScreenUtilInit(
      designSize: const Size(375, 812), // Design base no iPhone X
      minTextAdapt: true,
      splitScreenMode: true,
      builder: (context, child) {
        return MaterialApp.router(
          title: AppConstants.appName,
          debugShowCheckedModeBanner: false,
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.lightTheme, // Usando o mesmo tema para evitar mudanças
          themeMode: ThemeMode.light, // Forçando tema claro
          routerConfig: router,
        );
      },
    );
  }
}