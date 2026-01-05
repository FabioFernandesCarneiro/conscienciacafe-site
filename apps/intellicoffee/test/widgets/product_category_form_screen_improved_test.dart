import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intellicoffee/features/products/presentation/screens/product_category_form_screen_improved.dart';

void main() {
  testWidgets('ProductCategoryFormScreenImproved renders sections', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: ScreenUtilInit(
          designSize: const Size(375, 812),
          builder: (context, child) => const MaterialApp(
            home: ProductCategoryFormScreenImproved(),
          ),
        ),
      ),
    );

    await tester.pump();
    expect(find.textContaining('Categoria'), findsWidgets);
    expect(find.textContaining('Informações Básicas'), findsOneWidget);
    expect(find.textContaining('Campos Personalizados'), findsOneWidget);
  });
}

