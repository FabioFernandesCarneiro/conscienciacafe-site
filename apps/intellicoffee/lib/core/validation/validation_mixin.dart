import 'package:flutter/material.dart';
import 'package:intellicoffee/core/validation/form_validator.dart';
import 'package:intellicoffee/core/validation/validator.dart';

/// Mixin para facilitar validação em formulários
mixin ValidationMixin<T extends StatefulWidget> on State<T> {
  late final FormValidator _formValidator;
  bool _autoValidate = false;

  /// Inicializa o validador de formulário
  @override
  void initState() {
    super.initState();
    _formValidator = FormValidator();
    setupValidators();
  }

  /// Método para configurar validadores - deve ser implementado pelas classes filhas
  void setupValidators();

  /// FormValidator getter
  FormValidator get validator => _formValidator;

  /// Define se deve validar automaticamente
  set autoValidate(bool value) {
    _autoValidate = value;
    if (_autoValidate) {
      setState(() {
        _formValidator.validateAll();
      });
    }
  }

  /// Obtém se está em modo de validação automática
  bool get autoValidate => _autoValidate;

  /// Adiciona um validador para um campo
  void addValidator(String fieldName, Validator validator) {
    _formValidator.addValidator(fieldName, validator);
  }

  /// Define valor e valida se necessário
  void setValue(String fieldName, dynamic value) {
    _formValidator.setValue(fieldName, value);
    if (_autoValidate) {
      setState(() {});
    }
  }

  /// Obtém erro de um campo
  String? getError(String fieldName) {
    return _formValidator.getError(fieldName);
  }

  /// Verifica se o formulário é válido
  bool get isFormValid => _formValidator.isValid;

  /// Valida todo o formulário
  bool validateForm() {
    setState(() {
      _autoValidate = true;
    });
    return _formValidator.validateAll();
  }

  /// Limpa todos os erros
  void clearErrors() {
    setState(() {
      _formValidator.clearErrors();
      _autoValidate = false;
    });
  }

  /// Redefine o formulário
  void resetForm() {
    setState(() {
      _formValidator.reset();
      _autoValidate = false;
    });
  }

  /// Helper para criar TextFormField com validação
  Widget buildValidatedTextField({
    required String fieldName,
    required String label,
    String? hint,
    IconData? icon,
    bool obscureText = false,
    TextInputType? keyboardType,
    int? maxLines = 1,
    int? maxLength,
    bool readOnly = false,
    VoidCallback? onTap,
    void Function(String)? onChanged,
    TextEditingController? controller,
    Widget? suffix,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextFormField(
          controller: controller,
          obscureText: obscureText,
          keyboardType: keyboardType,
          maxLines: maxLines,
          maxLength: maxLength,
          readOnly: readOnly,
          onTap: onTap,
          decoration: InputDecoration(
            labelText: label,
            hintText: hint,
            prefixIcon: icon != null ? Icon(icon) : null,
            suffixIcon: suffix,
            errorText: getError(fieldName),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          onChanged: (value) {
            setValue(fieldName, value);
            onChanged?.call(value);
          },
        ),
      ],
    );
  }

  /// Helper para criar DropdownButtonFormField com validação
  Widget buildValidatedDropdown<V>({
    required String fieldName,
    required String label,
    required List<DropdownMenuItem<V>> items,
    V? value,
    String? hint,
    IconData? icon,
    void Function(V?)? onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownButtonFormField<V>(
          initialValue: value,
          items: items,
          decoration: InputDecoration(
            labelText: label,
            hintText: hint,
            prefixIcon: icon != null ? Icon(icon) : null,
            errorText: getError(fieldName),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          onChanged: (newValue) {
            setValue(fieldName, newValue);
            onChanged?.call(newValue);
          },
        ),
      ],
    );
  }

  /// Helper para criar Checkbox com validação
  Widget buildValidatedCheckbox({
    required String fieldName,
    required String label,
    bool value = false,
    void Function(bool?)? onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CheckboxListTile(
          title: Text(label),
          value: value,
          onChanged: (newValue) {
            setValue(fieldName, newValue ?? false);
            onChanged?.call(newValue);
          },
          controlAffinity: ListTileControlAffinity.leading,
        ),
        if (getError(fieldName) != null)
          Padding(
            padding: const EdgeInsets.only(left: 16, top: 4),
            child: Text(
              getError(fieldName)!,
              style: TextStyle(
                color: Theme.of(context).colorScheme.error,
                fontSize: 12,
              ),
            ),
          ),
      ],
    );
  }

  /// Helper para criar Switch com validação
  Widget buildValidatedSwitch({
    required String fieldName,
    required String label,
    bool value = false,
    void Function(bool)? onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SwitchListTile(
          title: Text(label),
          value: value,
          onChanged: (newValue) {
            setValue(fieldName, newValue);
            onChanged?.call(newValue);
          },
        ),
        if (getError(fieldName) != null)
          Padding(
            padding: const EdgeInsets.only(left: 16, top: 4),
            child: Text(
              getError(fieldName)!,
              style: TextStyle(
                color: Theme.of(context).colorScheme.error,
                fontSize: 12,
              ),
            ),
          ),
      ],
    );
  }

  /// Helper para criar botão de submit
  Widget buildSubmitButton({
    required String label,
    required VoidCallback onPressed,
    IconData? icon,
    bool enableValidation = true,
  }) {
    return ElevatedButton.icon(
      onPressed: () {
        if (enableValidation && !validateForm()) {
          return;
        }
        onPressed();
      },
      icon: icon != null ? Icon(icon) : const SizedBox.shrink(),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(double.infinity, 48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }
}