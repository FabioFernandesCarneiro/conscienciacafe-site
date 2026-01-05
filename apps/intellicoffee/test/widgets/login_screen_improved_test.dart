import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intellicoffee/features/auth/presentation/screens/login_screen_improved.dart';

void main() {
  testWidgets('LoginScreenImproved renders key elements', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: ScreenUtilInit(
          designSize: const Size(375, 812),
          minTextAdapt: true,
          splitScreenMode: true,
          builder: (context, child) => const MaterialApp(
            home: LoginScreenImproved(),
          ),
        ),
      ),
    );

    // Pump to allow layout
    await tester.pumpAndSettle();

    // Title and key buttons/labels
    expect(find.textContaining('IntelliCoffee'), findsOneWidget);
    expect(find.textContaining('Entrar'), findsWidgets);
    expect(find.textContaining('Esqueci minha senha'), findsOneWidget);
  });
}

