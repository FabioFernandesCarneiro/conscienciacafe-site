import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import 'package:intellicoffee/core/constants/app_constants.dart';
import 'package:intellicoffee/core/errors/error_notifier.dart';
import 'package:intellicoffee/core/validation/form_validator.dart';
import 'package:intellicoffee/core/validation/validation_mixin.dart';
import 'package:intellicoffee/features/auth/data/providers/auth_provider.dart';

/// Tela de login usando sistema de validação melhorado
class LoginScreenImproved extends ConsumerStatefulWidget {
  const LoginScreenImproved({super.key});

  @override
  ConsumerState<LoginScreenImproved> createState() => _LoginScreenImprovedState();
}

class _LoginScreenImprovedState extends ConsumerState<LoginScreenImproved> 
    with ValidationMixin {
  
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _rememberUser = false;
  bool _isLoading = false;
  bool _obscurePassword = true;

  @override
  void setupValidators() {
    // Email
    addValidator(
      'email',
      Validators.string()
          .required('E-mail é obrigatório')
          .email('E-mail inválido')
          .build(),
    );

    // Senha
    addValidator(
      'password',
      Validators.string()
          .required('Senha é obrigatória')
          .minLength(6, 'Senha deve ter pelo menos 6 caracteres')
          .build(),
    );
  }

  Future<void> _login() async {
    if (!validateForm()) {
      return;
    }

    setState(() => _isLoading = true);

    try {
      final authService = ref.read(authServiceProvider);
      await authService.signInWithEmailAndPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );
      
      if (mounted) {
        context.go(AppConstants.routeHome);
      }
    } catch (e, stackTrace) {
      // Usar o sistema global de erros
      ref.read(errorNotifierProvider.notifier).showError(e, stackTrace);
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: EdgeInsets.symmetric(horizontal: 32.w),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildLogo(),
                SizedBox(height: 48.h),
                _buildLoginForm(),
                SizedBox(height: 32.h),
                _buildLoginButton(),
                SizedBox(height: 24.h),
                _buildRememberMeSection(),
                SizedBox(height: 32.h),
                _buildForgotPasswordLink(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLogo() {
    return Column(
      children: [
        Container(
          width: 120.r,
          height: 120.r,
          decoration: BoxDecoration(
            color: const Color(0xFF4CAF50),
            borderRadius: BorderRadius.circular(20.r),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.1),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Icon(
            Icons.coffee,
            size: 60.r,
            color: Colors.white,
          ),
        ),
        SizedBox(height: 24.h),
        Text(
          'IntelliCoffee',
          style: TextStyle(
            fontSize: 32.sp,
            fontWeight: FontWeight.bold,
            color: const Color(0xFF2E2E2E),
          ),
        ),
        SizedBox(height: 8.h),
        Text(
          'Sistema de Gestão',
          style: TextStyle(
            fontSize: 16.sp,
            color: Colors.grey[600],
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildLoginForm() {
    return Container(
      padding: EdgeInsets.all(24.r),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 20,
            offset: const Offset(0, 5),
          ),
        ],
        border: Border.all(
          color: Colors.grey[200]!,
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Acesse sua conta',
            style: TextStyle(
              fontSize: 20.sp,
              fontWeight: FontWeight.w600,
              color: const Color(0xFF2E2E2E),
            ),
          ),
          SizedBox(height: 24.h),
          
          // Campo de email
          buildValidatedTextField(
            fieldName: 'email',
            label: 'E-mail',
            hint: 'seu@email.com',
            icon: Icons.email_outlined,
            keyboardType: TextInputType.emailAddress,
            controller: _emailController,
            onChanged: (value) => setValue('email', value),
          ),
          SizedBox(height: 16.h),
          
          // Campo de senha
          buildValidatedTextField(
            fieldName: 'password',
            label: 'Senha',
            hint: 'Digite sua senha',
            icon: Icons.lock_outlined,
            obscureText: _obscurePassword,
            controller: _passwordController,
            suffix: IconButton(
              icon: Icon(
                _obscurePassword ? Icons.visibility : Icons.visibility_off,
                color: Colors.grey[400],
              ),
              onPressed: () {
                setState(() => _obscurePassword = !_obscurePassword);
              },
            ),
            onChanged: (value) => setValue('password', value),
          ),
        ],
      ),
    );
  }

  Widget _buildLoginButton() {
    return buildSubmitButton(
      label: 'Entrar',
      icon: Icons.login,
      onPressed: _isLoading ? () {} : _login,
    );
  }

  Widget _buildRememberMeSection() {
    return Row(
      children: [
        Checkbox(
          value: _rememberUser,
          onChanged: (value) {
            setState(() => _rememberUser = value ?? false);
          },
          activeColor: const Color(0xFF4CAF50),
        ),
        Expanded(
          child: Text(
            'Lembrar-me neste dispositivo',
            style: TextStyle(
              fontSize: 14.sp,
              color: Colors.grey[600],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildForgotPasswordLink() {
    return TextButton(
      onPressed: _showForgotPasswordDialog,
      style: TextButton.styleFrom(
        foregroundColor: const Color(0xFF4CAF50),
      ),
      child: Text(
        'Esqueci minha senha',
        style: TextStyle(
          fontSize: 14.sp,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  void _showForgotPasswordDialog() {
    showDialog(
      context: context,
      builder: (context) => _ForgotPasswordDialog(),
    );
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}

/// Dialog para recuperação de senha
class _ForgotPasswordDialog extends ConsumerStatefulWidget {
  @override
  ConsumerState<_ForgotPasswordDialog> createState() => _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends ConsumerState<_ForgotPasswordDialog> 
    with ValidationMixin {
  
  final _emailController = TextEditingController();
  bool _isLoading = false;

  @override
  void setupValidators() {
    addValidator(
      'email',
      Validators.string()
          .required('E-mail é obrigatório')
          .email('E-mail inválido')
          .build(),
    );
  }

  Future<void> _sendPasswordReset() async {
    if (!validateForm()) return;

    setState(() => _isLoading = true);

    try {
      await FirebaseAuth.instance.sendPasswordResetEmail(
        email: _emailController.text.trim(),
      );
      
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('E-mail de recuperação enviado! Verifique sua caixa de entrada.'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e, stackTrace) {
      ref.read(errorNotifierProvider.notifier).showError(e, stackTrace);
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Recuperar Senha'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Digite seu e-mail para receber as instruções de recuperação de senha.',
            style: TextStyle(
              fontSize: 14.sp,
              color: Colors.grey[600],
            ),
          ),
          SizedBox(height: 16.h),
          
          buildValidatedTextField(
            fieldName: 'email',
            label: 'E-mail',
            hint: 'seu@email.com',
            icon: Icons.email_outlined,
            keyboardType: TextInputType.emailAddress,
            controller: _emailController,
            onChanged: (value) => setValue('email', value),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        ElevatedButton(
          onPressed: _isLoading ? null : _sendPasswordReset,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF4CAF50),
            foregroundColor: Colors.white,
          ),
          child: _isLoading
              ? SizedBox(
                  width: 20.r,
                  height: 20.r,
                  child: const CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : const Text('Enviar'),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }
}