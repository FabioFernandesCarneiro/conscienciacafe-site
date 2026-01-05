import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intellicoffee/core/errors/error_notifier.dart';
import 'package:intellicoffee/core/validation/form_validator.dart';
import 'package:intellicoffee/core/validation/validation_mixin.dart';
import 'package:intellicoffee/features/auth/data/providers/auth_provider.dart';

/// Dialog melhorado para alteração de senha usando sistema de validação
class ChangePasswordDialog extends ConsumerStatefulWidget {
  const ChangePasswordDialog({super.key});

  @override
  ConsumerState<ChangePasswordDialog> createState() => _ChangePasswordDialogState();
}

class _ChangePasswordDialogState extends ConsumerState<ChangePasswordDialog> 
    with ValidationMixin {
  
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  bool _obscureCurrentPassword = true;
  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;
  bool _isLoading = false;

  @override
  void setupValidators() {
    // Senha atual
    addValidator(
      'currentPassword',
      Validators.string()
          .required('Senha atual é obrigatória')
          .minLength(6, 'Senha deve ter pelo menos 6 caracteres')
          .build(),
    );

    // Nova senha
    addValidator(
      'newPassword',
      Validators.string()
          .required('Nova senha é obrigatória')
          .minLength(8, 'Nova senha deve ter pelo menos 8 caracteres')
          .pattern(
            RegExp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)'),
            'Nova senha deve conter pelo menos: 1 letra minúscula, 1 maiúscula e 1 número',
          )
          .build(),
    );

    // Validação adicional para nova senha diferente da atual  
    addValidator(
      'newPasswordDifferent',
      Validators.custom<String>((value) {
        if (value == _currentPasswordController.text) {
          return 'Nova senha deve ser diferente da senha atual';
        }
        return null;
      }),
    );

    // Confirmação de senha
    addValidator(
      'confirmPassword',
      Validators.string()
          .required('Confirmação de senha é obrigatória')
          .build(),
    );

    // Validação adicional para confirmação de senha
    addValidator(
      'confirmPasswordMatch',
      Validators.custom<String>((value) {
        if (value != _newPasswordController.text) {
          return 'Senhas não conferem';
        }
        return null;
      }),
    );
  }

  Future<void> _changePassword() async {
    if (!validateForm()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Por favor, corrija os erros no formulário'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final authService = ref.read(authServiceProvider);
      
      // Alterar senha usando o serviço de autenticação
      await authService.changePassword(
        currentPassword: _currentPasswordController.text,
        newPassword: _newPasswordController.text,
      );
      
      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Senha alterada com sucesso!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e, stackTrace) {
      // Usar sistema global de erros
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
      backgroundColor: Colors.grey[50],
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16.r),
      ),
      title: Row(
        children: [
          Icon(
            Icons.lock_outline,
            color: const Color(0xFF4CAF50),
            size: 24.r,
          ),
          SizedBox(width: 8.w),
          const Text('Alterar Senha'),
        ],
      ),
      content: SingleChildScrollView(
        child: SizedBox(
          width: 300.w,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Para sua segurança, confirme sua senha atual antes de definir uma nova.',
                style: TextStyle(
                  fontSize: 14.sp,
                  color: Colors.grey[600],
                ),
              ),
              SizedBox(height: 24.h),
              
              _buildPasswordField(
                fieldName: 'currentPassword',
                controller: _currentPasswordController,
                label: 'Senha Atual',
                hint: 'Digite sua senha atual',
                icon: Icons.lock,
                obscureText: _obscureCurrentPassword,
                onToggleVisibility: () {
                  setState(() => _obscureCurrentPassword = !_obscureCurrentPassword);
                },
                onChanged: (value) {
                  setValue('currentPassword', value);
                  // Re-validar nova senha se foi alterada
                  if (_newPasswordController.text.isNotEmpty) {
                    setValue('newPassword', _newPasswordController.text);
                  }
                },
              ),
              SizedBox(height: 16.h),
              
              _buildPasswordField(
                fieldName: 'newPassword',
                controller: _newPasswordController,
                label: 'Nova Senha',
                hint: 'Digite sua nova senha',
                icon: Icons.lock_outlined,
                obscureText: _obscureNewPassword,
                onToggleVisibility: () {
                  setState(() => _obscureNewPassword = !_obscureNewPassword);
                },
                onChanged: (value) {
                  setValue('newPassword', value);
                  // Re-validar confirmação se foi preenchida
                  if (_confirmPasswordController.text.isNotEmpty) {
                    setValue('confirmPassword', _confirmPasswordController.text);
                  }
                },
              ),
              SizedBox(height: 16.h),
              
              _buildPasswordField(
                fieldName: 'confirmPassword',
                controller: _confirmPasswordController,
                label: 'Confirmar Nova Senha',
                hint: 'Digite novamente a nova senha',
                icon: Icons.lock_outlined,
                obscureText: _obscureConfirmPassword,
                onToggleVisibility: () {
                  setState(() => _obscureConfirmPassword = !_obscureConfirmPassword);
                },
                onChanged: (value) => setValue('confirmPassword', value),
              ),
              SizedBox(height: 16.h),
              
              _buildPasswordRequirements(),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancelar'),
        ),
        ElevatedButton(
          onPressed: _isLoading ? null : _changePassword,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF4CAF50),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8.r),
            ),
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
              : const Text('Alterar Senha'),
        ),
      ],
    );
  }

  Widget _buildPasswordField({
    required String fieldName,
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    required bool obscureText,
    required VoidCallback onToggleVisibility,
    required Function(String) onChanged,
  }) {
    final error = getError(fieldName);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: controller,
          obscureText: obscureText,
          onChanged: onChanged,
          decoration: InputDecoration(
            labelText: label,
            hintText: hint,
            prefixIcon: Icon(icon, color: Colors.grey[400]),
            suffixIcon: IconButton(
              icon: Icon(
                obscureText ? Icons.visibility_off : Icons.visibility,
                color: Colors.grey[400],
              ),
              onPressed: onToggleVisibility,
            ),
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: error != null ? Colors.red : Colors.grey[300]!,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: error != null ? Colors.red : Colors.grey[300]!,
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: error != null ? Colors.red : const Color(0xFF4CAF50),
                width: 2,
              ),
            ),
            errorText: error,
            errorMaxLines: 2,
          ),
        ),
      ],
    );
  }

  Widget _buildPasswordRequirements() {
    return Container(
      padding: EdgeInsets.all(12.r),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(8.r),
        border: Border.all(color: Colors.blue[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.info_outline,
                size: 16.r,
                color: Colors.blue[700],
              ),
              SizedBox(width: 8.w),
              Text(
                'Requisitos da nova senha:',
                style: TextStyle(
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w600,
                  color: Colors.blue[700],
                ),
              ),
            ],
          ),
          SizedBox(height: 8.h),
          _buildRequirement('Pelo menos 8 caracteres'),
          _buildRequirement('1 letra minúscula (a-z)'),
          _buildRequirement('1 letra maiúscula (A-Z)'),
          _buildRequirement('1 número (0-9)'),
          _buildRequirement('Diferente da senha atual'),
        ],
      ),
    );
  }

  Widget _buildRequirement(String text) {
    return Padding(
      padding: EdgeInsets.only(left: 16.w, bottom: 4.h),
      child: Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 12.r,
            color: Colors.blue[600],
          ),
          SizedBox(width: 8.w),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 11.sp,
                color: Colors.blue[600],
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }
}