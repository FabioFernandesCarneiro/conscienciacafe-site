import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intellicoffee/core/errors/error_notifier.dart';

/// Widget para exibir erros globais da aplicação
class GlobalErrorListener extends ConsumerWidget {
  final Widget child;

  const GlobalErrorListener({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Escuta mudanças no estado de erro
    ref.listen(errorNotifierProvider, (previous, next) {
      if (next.isVisible && next.currentError != null) {
        _showErrorSnackBar(context, ref, next);
      }
    });

    return child;
  }

  void _showErrorSnackBar(
    BuildContext context,
    WidgetRef ref,
    ErrorNotificationState errorState,
  ) {
    final errorNotifier = ref.read(errorNotifierProvider.notifier);
    final message = errorNotifier.displayMessage ?? 'Erro inesperado';
    final canRetry = errorNotifier.canRetry;
    final requiresReauth = errorNotifier.requiresReauth;

    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              Icons.error_outline,
              color: Colors.white,
              size: 20.r,
            ),
            SizedBox(width: 8.w),
            Expanded(
              child: Text(
                message,
                style: TextStyle(
                  fontSize: 14.sp,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
        backgroundColor: Colors.red[700],
        duration: const Duration(seconds: 6),
        behavior: SnackBarBehavior.floating,
        margin: EdgeInsets.all(16.r),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8.r),
        ),
        action: _buildSnackBarAction(context, ref, canRetry, requiresReauth),
      ),
    );

    // Auto-clear após mostrar
    Future.delayed(const Duration(seconds: 6), () {
      errorNotifier.clearError();
    });
  }

  SnackBarAction? _buildSnackBarAction(
    BuildContext context,
    WidgetRef ref,
    bool canRetry,
    bool requiresReauth,
  ) {
    final errorNotifier = ref.read(errorNotifierProvider.notifier);

    if (requiresReauth) {
      return SnackBarAction(
        label: 'LOGIN',
        textColor: Colors.white,
        onPressed: () {
          errorNotifier.clearError();
          // Navegar para tela de login
          // Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
        },
      );
    }

    if (canRetry) {
      return SnackBarAction(
        label: 'TENTAR NOVAMENTE',
        textColor: Colors.white,
        onPressed: () {
          errorNotifier.clearError();
          // Implementar lógica de retry se necessário
        },
      );
    }

    return SnackBarAction(
      label: 'OK',
      textColor: Colors.white,
      onPressed: () {
        errorNotifier.clearError();
      },
    );
  }
}

/// Widget para exibir estado de erro em uma tela específica
class ErrorStateWidget extends StatelessWidget {
  final String? message;
  final VoidCallback? onRetry;
  final bool showRetryButton;
  final IconData? icon;

  const ErrorStateWidget({
    super.key,
    this.message,
    this.onRetry,
    this.showRetryButton = true,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(32.r),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon ?? Icons.error_outline,
              size: 64.r,
              color: Colors.red[300],
            ),
            SizedBox(height: 24.h),
            Text(
              message ?? 'Ocorreu um erro inesperado',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16.sp,
                color: Colors.grey[700],
              ),
            ),
            if (showRetryButton && onRetry != null) ...[
              SizedBox(height: 24.h),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: Icon(Icons.refresh, size: 18.r),
                label: Text(
                  'Tentar Novamente',
                  style: TextStyle(fontSize: 14.sp),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).primaryColor,
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(
                    horizontal: 24.w,
                    vertical: 12.h,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Widget para exibir erros inline em formulários
class InlineErrorWidget extends StatelessWidget {
  final String? error;
  final EdgeInsetsGeometry? padding;

  const InlineErrorWidget({
    super.key,
    this.error,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    if (error == null || error!.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: padding ?? EdgeInsets.only(top: 8.h),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.error_outline,
            size: 16.r,
            color: Colors.red,
          ),
          SizedBox(width: 8.w),
          Expanded(
            child: Text(
              error!,
              style: TextStyle(
                fontSize: 12.sp,
                color: Colors.red,
              ),
            ),
          ),
        ],
      ),
    );
  }
}