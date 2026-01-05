import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class AppTheme {
  // Colors
  static const Color primaryColor = Color(0xFF4CAF50); // Green
  static const Color secondaryColor = Color(0xFF2196F3); // Blue
  static const Color backgroundColor = Colors.white;
  static const Color surfaceColor = Color(0xFFF5F5F5); // Light gray
  static const Color cardColor = Colors.white;
  static const Color borderColor = Color(0xFFE0E0E0); // Light gray border
  static const Color errorColor = Color(0xFFD32F2F); // Red

  // Text colors
  static const Color textPrimaryColor = Color(0xFF212121); // Dark gray
  static const Color textSecondaryColor = Color(0xFF757575); // Medium gray
  static const Color textTertiaryColor = Color(0xFF9E9E9E); // Light gray

  static ThemeData get lightTheme {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        brightness: Brightness.light,
        surface: Colors.grey[50]!,
      ),
      useMaterial3: true,
      scaffoldBackgroundColor: backgroundColor,
      
      // AppBar Theme
      appBarTheme: const AppBarTheme(
        backgroundColor: backgroundColor,
        foregroundColor: textPrimaryColor,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: textPrimaryColor,
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
      ),
      
      // Card Theme
      cardTheme: CardThemeData(
        color: cardColor,
        elevation: 0,
        margin: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8.r),
          side: BorderSide(color: borderColor, width: 1),
        ),
      ),
      
      // Input Decoration Theme
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.r),
          borderSide: BorderSide(color: borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.r),
          borderSide: BorderSide(color: borderColor),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.r),
          borderSide: const BorderSide(color: primaryColor, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8.r),
          borderSide: const BorderSide(color: errorColor),
        ),
        contentPadding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
        labelStyle: TextStyle(
          color: textSecondaryColor,
          fontSize: 10.sp,
        ),
        hintStyle: TextStyle(
          color: textTertiaryColor,
          fontSize: 10.sp,
        ),
      ),
      
      // Button Themes
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 14.h),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8.r),
          ),
          textStyle: TextStyle(
            fontSize: 10.sp,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
      
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primaryColor,
          side: const BorderSide(color: primaryColor),
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 14.h),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8.r),
          ),
          textStyle: TextStyle(
            fontSize: 10.sp,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
      
      // Text Theme
      textTheme: TextTheme(
        displayLarge: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.bold, color: textPrimaryColor),
        displayMedium: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.bold, color: textPrimaryColor),
        displaySmall: TextStyle(fontSize: 14.sp, fontWeight: FontWeight.bold, color: textPrimaryColor),
        headlineMedium: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.bold, color: textPrimaryColor),
        titleLarge: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w600, color: textPrimaryColor),
        bodyLarge: TextStyle(fontSize: 10.sp, color: textPrimaryColor),
        bodyMedium: TextStyle(fontSize: 10.sp, color: textSecondaryColor),
      ),
      
      // List Tile Theme
      listTileTheme: const ListTileThemeData(
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        tileColor: cardColor,
      ),
      
      // Switch Theme
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith<Color>((states) {
          if (states.contains(WidgetState.selected)) {
            return primaryColor;
          }
          return Colors.grey;
        }),
        trackColor: WidgetStateProperty.resolveWith<Color>((states) {
          if (states.contains(WidgetState.selected)) {
            return primaryColor.withValues(alpha: 0.3);
          }
          return Colors.grey.withValues(alpha: 0.3);
        }),
      ),
      
      // Checkbox Theme
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith<Color>((states) {
          if (states.contains(WidgetState.selected)) {
            return primaryColor;
          }
          return Colors.transparent;
        }),
        side: BorderSide(color: borderColor),
      ),
    );
  }

  // Temas específicos para cada módulo - Mantendo a cor primária verde para todos
  static ThemeData get atendimentoTheme => lightTheme;
  static ThemeData get clientesTheme => lightTheme;
  static ThemeData get torrefacaoTheme => lightTheme;
  static ThemeData get vendasB2BTheme => lightTheme;
  static ThemeData get eventosTheme => lightTheme;
  static ThemeData get gestaoTheme => lightTheme;
}