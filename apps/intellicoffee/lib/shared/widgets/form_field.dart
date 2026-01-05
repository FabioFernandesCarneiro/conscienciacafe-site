import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intl/intl.dart';

/// Campo de formulário padronizado com estilo consistente para o IntelliCoffee.
///
/// Este widget fornece um campo de texto estilizado de acordo com o design system
/// do IntelliCoffee, incluindo formatação de rótulos, animações de foco,
/// e funcionalidades de validação.
class AppFormField extends StatelessWidget {
  final String? label;
  final String? hint;
  final String? errorText;
  final TextEditingController? controller;
  final FocusNode? focusNode;
  final ValueChanged<String>? onChanged;
  final FormFieldValidator<String>? validator;
  final TextInputType keyboardType;
  final bool obscureText;
  final bool readOnly;
  final bool required;
  final Widget? prefix;
  final Widget? suffix;
  final int? maxLines;
  final int? maxLength;
  final String? counterText;
  final bool showCounter;
  final List<TextInputFormatter>? inputFormatters;
  final TextCapitalization textCapitalization;
  final TextInputAction? textInputAction;
  final VoidCallback? onTap;
  final bool autofocus;
  final AutovalidateMode autovalidateMode;
  final bool enabled;
  final String? initialValue;
  final EdgeInsetsGeometry? contentPadding;
  final String? helperText;
  final bool filled;
  final Color? fillColor;

  const AppFormField({
    super.key,
    this.label,
    this.hint,
    this.errorText,
    this.controller,
    this.focusNode,
    this.onChanged,
    this.validator,
    this.keyboardType = TextInputType.text,
    this.obscureText = false,
    this.readOnly = false,
    this.required = false,
    this.prefix,
    this.suffix,
    this.maxLines = 1,
    this.maxLength,
    this.counterText,
    this.showCounter = false,
    this.inputFormatters,
    this.textCapitalization = TextCapitalization.none,
    this.textInputAction,
    this.onTap,
    this.autofocus = false,
    this.autovalidateMode = AutovalidateMode.onUserInteraction,
    this.enabled = true,
    this.initialValue,
    this.contentPadding,
    this.helperText,
    this.filled = true,
    this.fillColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null)
          Padding(
            padding: EdgeInsets.only(bottom: 4.h),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                RichText(
                  text: TextSpan(
                    text: label,
                    style: TextStyle(
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w500,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
                    ),
                    children: [
                      if (required)
                        TextSpan(
                          text: ' *',
                          style: TextStyle(
                            color: theme.colorScheme.error,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                    ],
                  ),
                ),
                if (counterText != null)
                  Text(
                    counterText!,
                    style: TextStyle(
                      fontSize: 10.sp,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                    ),
                  ),
              ],
            ),
          ),
        TextFormField(
          controller: controller,
          focusNode: focusNode,
          onChanged: onChanged,
          validator: validator,
          keyboardType: keyboardType,
          obscureText: obscureText,
          readOnly: readOnly,
          maxLines: maxLines,
          maxLength: maxLength,
          inputFormatters: inputFormatters,
          textCapitalization: textCapitalization,
          textInputAction: textInputAction,
          onTap: onTap,
          autofocus: autofocus,
          autovalidateMode: autovalidateMode,
          enabled: enabled,
          initialValue: initialValue,
          style: TextStyle(
            fontSize: 12.sp,
            color: theme.colorScheme.onSurface,
          ),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(
              fontSize: 12.sp,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            errorText: errorText,
            prefixIcon: prefix,
            suffixIcon: suffix,
            contentPadding: contentPadding ?? EdgeInsets.all(16.r),
            counterText: showCounter ? null : '',
            helperText: helperText,
            helperStyle: TextStyle(
              fontSize: 10.sp,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            filled: filled,
            fillColor: fillColor ?? Colors.white,
            focusColor: Colors.white,
            hoverColor: Colors.white,
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.primary,
                width: 2.0,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.3),
                width: 1.0,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.error,
                width: 1.0,
              ),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.error,
                width: 2.0,
              ),
            ),
            disabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.2),
                width: 1.0,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// Campo de formulário para entrada de e-mail com validação.
class AppEmailField extends StatelessWidget {
  final String label;
  final String hint;
  final String? errorText;
  final TextEditingController? controller;
  final FocusNode? focusNode;
  final ValueChanged<String>? onChanged;
  final FormFieldValidator<String>? validator;
  final bool required;
  final bool readOnly;
  final bool enabled;
  final TextInputAction? textInputAction;

  const AppEmailField({
    super.key,
    this.label = 'E-mail',
    this.hint = 'Digite seu e-mail',
    this.errorText,
    this.controller,
    this.focusNode,
    this.onChanged,
    this.validator,
    this.required = true,
    this.readOnly = false,
    this.enabled = true,
    this.textInputAction = TextInputAction.next,
  });

  @override
  Widget build(BuildContext context) {
    return AppFormField(
      label: label,
      hint: hint,
      errorText: errorText,
      controller: controller,
      focusNode: focusNode,
      onChanged: onChanged,
      validator: validator ?? _defaultValidator,
      keyboardType: TextInputType.emailAddress,
      required: required,
      readOnly: readOnly,
      enabled: enabled,
      textInputAction: textInputAction,
      prefix: Icon(
        Icons.email_outlined,
        size: 20.r,
        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
      ),
    );
  }

  String? _defaultValidator(String? value) {
    if (value == null || value.isEmpty) {
      return 'Digite seu e-mail';
    }
    if (!RegExp(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        .hasMatch(value)) {
      return 'Digite um e-mail válido';
    }
    return null;
  }
}

/// Campo de formulário para entrada de senha com toggle de visibilidade.
class AppPasswordField extends StatefulWidget {
  final String label;
  final String hint;
  final String? errorText;
  final String? helperText;
  final TextEditingController? controller;
  final FocusNode? focusNode;
  final ValueChanged<String>? onChanged;
  final FormFieldValidator<String>? validator;
  final bool required;
  final bool readOnly;
  final bool enabled;
  final TextInputAction? textInputAction;

  const AppPasswordField({
    super.key,
    this.label = 'Senha',
    this.hint = 'Digite sua senha',
    this.errorText,
    this.helperText,
    this.controller,
    this.focusNode,
    this.onChanged,
    this.validator,
    this.required = true,
    this.readOnly = false,
    this.enabled = true,
    this.textInputAction = TextInputAction.done,
  });

  @override
  State<AppPasswordField> createState() => _AppPasswordFieldState();
}

class _AppPasswordFieldState extends State<AppPasswordField> {
  bool _obscureText = true;

  @override
  Widget build(BuildContext context) {
    return AppFormField(
      label: widget.label,
      hint: widget.hint,
      errorText: widget.errorText,
      helperText: widget.helperText,
      controller: widget.controller,
      focusNode: widget.focusNode,
      onChanged: widget.onChanged,
      validator: widget.validator ?? _defaultValidator,
      keyboardType: TextInputType.visiblePassword,
      obscureText: _obscureText,
      required: widget.required,
      readOnly: widget.readOnly,
      enabled: widget.enabled,
      textInputAction: widget.textInputAction,
      prefix: Icon(
        Icons.lock_outline,
        size: 20.r,
        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
      ),
      suffix: IconButton(
        icon: Icon(
          _obscureText ? Icons.visibility : Icons.visibility_off,
          size: 20.r,
          color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
        ),
        onPressed: () {
          setState(() {
            _obscureText = !_obscureText;
          });
        },
      ),
    );
  }

  String? _defaultValidator(String? value) {
    if (value == null || value.isEmpty) {
      return 'Digite sua senha';
    }
    if (value.length < 6) {
      return 'A senha deve ter pelo menos 6 caracteres';
    }
    return null;
  }
}

/// Campo de formulário para entrada de telefone com formatação.
class AppPhoneField extends StatelessWidget {
  final String label;
  final String hint;
  final String? errorText;
  final TextEditingController? controller;
  final FocusNode? focusNode;
  final ValueChanged<String>? onChanged;
  final FormFieldValidator<String>? validator;
  final bool required;
  final bool readOnly;
  final bool enabled;
  final TextInputAction? textInputAction;

  const AppPhoneField({
    super.key,
    this.label = 'Telefone',
    this.hint = '(00) 00000-0000',
    this.errorText,
    this.controller,
    this.focusNode,
    this.onChanged,
    this.validator,
    this.required = false,
    this.readOnly = false,
    this.enabled = true,
    this.textInputAction = TextInputAction.next,
  });

  @override
  Widget build(BuildContext context) {
    return AppFormField(
      label: label,
      hint: hint,
      errorText: errorText,
      controller: controller,
      focusNode: focusNode,
      onChanged: onChanged,
      validator: validator,
      keyboardType: TextInputType.phone,
      required: required,
      readOnly: readOnly,
      enabled: enabled,
      textInputAction: textInputAction,
      inputFormatters: [
        FilteringTextInputFormatter.digitsOnly,
        _PhoneInputFormatter(),
      ],
      prefix: Icon(
        Icons.phone_outlined,
        size: 20.r,
        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
      ),
    );
  }
}

/// Formatador para transformar entrada de dígitos em formato de telefone brasileiro.
class _PhoneInputFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(
      TextEditingValue oldValue, TextEditingValue newValue) {
    final newText = newValue.text;
    
    if (newText.isEmpty) {
      return newValue;
    }
    
    final onlyDigits = newText.replaceAll(RegExp(r'[^\d]'), '');
    String formattedText;
    
    if (onlyDigits.length <= 2) {
      formattedText = '($onlyDigits';
    } else if (onlyDigits.length <= 7) {
      formattedText = '(${onlyDigits.substring(0, 2)}) ${onlyDigits.substring(2)}';
    } else if (onlyDigits.length <= 11) {
      formattedText = '(${onlyDigits.substring(0, 2)}) ${onlyDigits.substring(2, 7)}-${onlyDigits.substring(7)}';
    } else {
      formattedText = '(${onlyDigits.substring(0, 2)}) ${onlyDigits.substring(2, 7)}-${onlyDigits.substring(7, 11)}';
    }
    
    return TextEditingValue(
      text: formattedText,
      selection: TextSelection.collapsed(offset: formattedText.length),
    );
  }
}

/// Campo de formulário para seleção de data com DatePicker.
class AppDateField extends StatelessWidget {
  final String label;
  final String hint;
  final String? errorText;
  final TextEditingController controller;
  final FocusNode? focusNode;
  final ValueChanged<DateTime?>? onChanged;
  final FormFieldValidator<String>? validator;
  final bool required;
  final bool readOnly;
  final bool enabled;
  final DateTime? initialDate;
  final DateTime? firstDate;
  final DateTime? lastDate;
  final String format;

  const AppDateField({
    super.key,
    this.label = 'Data',
    this.hint = 'Selecione uma data',
    this.errorText,
    required this.controller,
    this.focusNode,
    this.onChanged,
    this.validator,
    this.required = false,
    this.readOnly = false,
    this.enabled = true,
    this.initialDate,
    this.firstDate,
    this.lastDate,
    this.format = 'dd/MM/yyyy',
  });

  @override
  Widget build(BuildContext context) {
    return AppFormField(
      label: label,
      hint: hint,
      errorText: errorText,
      controller: controller,
      focusNode: focusNode,
      validator: validator,
      keyboardType: TextInputType.datetime,
      required: required,
      readOnly: true,
      enabled: enabled,
      onTap: () async {
        if (readOnly || !enabled) return;
        
        final date = await _selectDate(context);
        if (date != null) {
          final formattedDate = DateFormat(format).format(date);
          controller.text = formattedDate;
          if (onChanged != null) {
            onChanged!(date);
          }
        }
      },
      prefix: Icon(
        Icons.calendar_today_outlined,
        size: 20.r,
        color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
      ),
    );
  }

  Future<DateTime?> _selectDate(BuildContext context) async {
    DateTime? initialDateValue;
    
    if (controller.text.isNotEmpty) {
      try {
        initialDateValue = DateFormat(format).parse(controller.text);
      } catch (e) {
        initialDateValue = initialDate ?? DateTime.now();
      }
    } else {
      initialDateValue = initialDate ?? DateTime.now();
    }
    
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: initialDateValue,
      firstDate: firstDate ?? DateTime(1900),
      lastDate: lastDate ?? DateTime(2100),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: ColorScheme.light(
              primary: Theme.of(context).colorScheme.primary,
              onPrimary: Theme.of(context).colorScheme.onPrimary,
              surface: Theme.of(context).colorScheme.surface,
              onSurface: Theme.of(context).colorScheme.onSurface,
            ),
          ),
          child: child!,
        );
      },
    );
    
    return picked;
  }
}

/// Campo de seleção dropdown estilizado.
class AppSelectField<T> extends StatelessWidget {
  final String? label;
  final String hint;
  final List<DropdownMenuItem<T>> items;
  final T? value;
  final ValueChanged<T?>? onChanged;
  final FormFieldValidator<T>? validator;
  final bool required;
  final bool enabled;
  final Widget? prefix;

  const AppSelectField({
    super.key,
    this.label,
    this.hint = 'Selecione uma opção',
    required this.items,
    this.value,
    this.onChanged,
    this.validator,
    this.required = false,
    this.enabled = true,
    this.prefix,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null)
          Padding(
            padding: EdgeInsets.only(bottom: 4.h),
            child: RichText(
              text: TextSpan(
                text: label,
                style: TextStyle(
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w500,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
                ),
                children: [
                  if (required)
                    TextSpan(
                      text: ' *',
                      style: TextStyle(
                        color: theme.colorScheme.error,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                ],
              ),
            ),
          ),
        DropdownButtonFormField<T>(
          initialValue: value,
          onChanged: enabled ? onChanged : null,
          validator: validator,
          isExpanded: true,
          icon: Icon(
            Icons.keyboard_arrow_down,
            size: 20.r,
            color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          ),
          iconSize: 24.0,
          elevation: 2,
          style: TextStyle(
            fontSize: 12.sp,
            color: theme.colorScheme.onSurface,
          ),
          dropdownColor: Colors.white,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(
              fontSize: 12.sp,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            prefixIcon: prefix,
            contentPadding: EdgeInsets.all(16.r),
            filled: true,
            fillColor: enabled 
                ? Colors.white 
                : theme.colorScheme.onSurface.withValues(alpha: 0.05),
            focusColor: Colors.white,
            hoverColor: Colors.white,
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.primary,
                width: 2.0,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.3),
                width: 1.0,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.error,
                width: 1.0,
              ),
            ),
            focusedErrorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.error,
                width: 2.0,
              ),
            ),
            disabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8.r),
              borderSide: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.2),
                width: 1.0,
              ),
            ),
          ),
          items: items,
        ),
      ],
    );
  }
}

/// Contador numérico com botões + e -.
class AppNumericField extends StatelessWidget {
  final String? label;
  final TextEditingController controller;
  final ValueChanged<int>? onChanged;
  final int min;
  final int max;
  final int step;
  final bool required;
  final bool enabled;
  final String? suffix;
  final FormFieldValidator<String>? validator;

  const AppNumericField({
    super.key,
    this.label,
    required this.controller,
    this.onChanged,
    this.min = 0,
    this.max = 999,
    this.step = 1,
    this.required = false,
    this.enabled = true,
    this.suffix,
    this.validator,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null)
          Padding(
            padding: EdgeInsets.only(bottom: 4.h),
            child: RichText(
              text: TextSpan(
                text: label,
                style: TextStyle(
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w500,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
                ),
                children: [
                  if (required)
                    TextSpan(
                      text: ' *',
                      style: TextStyle(
                        color: theme.colorScheme.error,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                ],
              ),
            ),
          ),
        Row(
          children: [
            Container(
              width: 40.w,
              height: 40.h,
              decoration: BoxDecoration(
                color: enabled
                    ? Colors.white
                    : theme.colorScheme.onSurface.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(8.r),
                border: Border.all(
                  color: theme.colorScheme.outline.withValues(alpha: 0.3),
                  width: 1.0,
                ),
              ),
              child: IconButton(
                icon: Icon(
                  Icons.remove,
                  size: 16.r,
                  color: enabled
                      ? theme.colorScheme.onSurface
                      : theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                padding: EdgeInsets.zero,
                onPressed: enabled
                    ? () {
                        final currentValue = int.tryParse(controller.text) ?? 0;
                        final newValue = (currentValue - step).clamp(min, max);
                        controller.text = newValue.toString();
                        if (onChanged != null) {
                          onChanged!(newValue);
                        }
                      }
                    : null,
              ),
            ),
            Expanded(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 8.w),
                child: TextFormField(
                  controller: controller,
                  keyboardType: TextInputType.number,
                  textAlign: TextAlign.center,
                  validator: validator,
                  enabled: enabled,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                  ],
                  onChanged: (value) {
                    final intValue = int.tryParse(value) ?? 0;
                    final clampedValue = intValue.clamp(min, max);
                    if (intValue != clampedValue) {
                      controller.text = clampedValue.toString();
                      controller.selection = TextSelection.fromPosition(
                        TextPosition(offset: controller.text.length),
                      );
                    }
                    if (onChanged != null) {
                      onChanged!(clampedValue);
                    }
                  },
                  decoration: InputDecoration(
                    contentPadding: EdgeInsets.symmetric(
                      vertical: 10.h,
                      horizontal: 12.w,
                    ),
                    filled: true,
                    fillColor: enabled
                        ? Colors.white
                        : theme.colorScheme.onSurface.withValues(alpha: 0.05),
                    focusColor: Colors.white,
                    hoverColor: Colors.white,
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                      borderSide: BorderSide(
                        color: theme.colorScheme.outline.withValues(alpha: 0.3),
                        width: 1.0,
                      ),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                      borderSide: BorderSide(
                        color: theme.colorScheme.primary,
                        width: 2.0,
                      ),
                    ),
                    disabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                      borderSide: BorderSide(
                        color: theme.colorScheme.outline.withValues(alpha: 0.2),
                        width: 1.0,
                      ),
                    ),
                  ),
                ),
              ),
            ),
            Container(
              width: 40.w,
              height: 40.h,
              decoration: BoxDecoration(
                color: enabled
                    ? Colors.white
                    : theme.colorScheme.onSurface.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(8.r),
                border: Border.all(
                  color: theme.colorScheme.outline.withValues(alpha: 0.3),
                  width: 1.0,
                ),
              ),
              child: IconButton(
                icon: Icon(
                  Icons.add,
                  size: 16.r,
                  color: enabled
                      ? theme.colorScheme.onSurface
                      : theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                padding: EdgeInsets.zero,
                onPressed: enabled
                    ? () {
                        final currentValue = int.tryParse(controller.text) ?? 0;
                        final newValue = (currentValue + step).clamp(min, max);
                        controller.text = newValue.toString();
                        if (onChanged != null) {
                          onChanged!(newValue);
                        }
                      }
                    : null,
              ),
            ),
            if (suffix != null)
              Container(
                margin: EdgeInsets.only(left: 8.w),
                padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 8.h),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.8),
                  borderRadius: BorderRadius.circular(8.r),
                  border: Border.all(
                    color: theme.colorScheme.outline.withValues(alpha: 0.2),
                    width: 1.0,
                  ),
                ),
                child: Text(
                  suffix!,
                  style: TextStyle(
                    fontSize: 12.sp,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }
}

/// Campo de toggle (switch) customizado.
class AppToggleField extends StatelessWidget {
  final String label;
  final bool value;
  final ValueChanged<bool>? onChanged;
  final String? description;
  final String activeText;
  final String inactiveText;
  final bool enabled;

  const AppToggleField({
    super.key,
    required this.label,
    required this.value,
    this.onChanged,
    this.description,
    this.activeText = 'Ativado',
    this.inactiveText = 'Desativado',
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: FontWeight.w500,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
              ),
            ),
            Row(
              children: [
                Text(
                  inactiveText,
                  style: TextStyle(
                    fontSize: 12.sp,
                    color: value
                        ? theme.colorScheme.onSurface.withValues(alpha: 0.5)
                        : theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
                SizedBox(width: 8.w),
                GestureDetector(
                  onTap: enabled
                      ? () {
                          if (onChanged != null) {
                            onChanged!(!value);
                          }
                        }
                      : null,
                  child: Container(
                    width: 50.w,
                    height: 24.h,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12.r),
                      color: value
                          ? theme.colorScheme.primary
                          : Colors.white,
                      border: Border.all(
                        color: value
                            ? theme.colorScheme.primary
                            : theme.colorScheme.outline.withValues(alpha: 0.3),
                        width: 1.0,
                      ),
                    ),
                    child: Stack(
                      children: [
                        AnimatedPositioned(
                          duration: const Duration(milliseconds: 150),
                          curve: Curves.easeInOut,
                          left: value ? 26.w : 2.w,
                          top: 2.h,
                          child: Container(
                            width: 18.w,
                            height: 18.h,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: value
                                  ? theme.colorScheme.onPrimary
                                  : theme.colorScheme.onSurface.withValues(alpha: 0.5),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(width: 8.w),
                Text(
                  activeText,
                  style: TextStyle(
                    fontSize: 12.sp,
                    color: value
                        ? theme.colorScheme.onSurface.withValues(alpha: 0.7)
                        : theme.colorScheme.onSurface.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ],
        ),
        if (description != null)
          Padding(
            padding: EdgeInsets.only(top: 4.h),
            child: Text(
              description!,
              style: TextStyle(
                fontSize: 12.sp,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
              ),
            ),
          ),
      ],
    );
  }
}

/// Campo de checkbox customizado.
class AppCheckboxField extends StatelessWidget {
  final String label;
  final bool value;
  final ValueChanged<bool?>? onChanged;
  final bool enabled;

  const AppCheckboxField({
    super.key,
    required this.label,
    required this.value,
    this.onChanged,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return InkWell(
      onTap: enabled
          ? () {
              if (onChanged != null) {
                onChanged!(!value);
              }
            }
          : null,
      borderRadius: BorderRadius.circular(8.r),
      child: Padding(
        padding: EdgeInsets.symmetric(vertical: 8.h),
        child: Row(
          children: [
            SizedBox(
              width: 20.w,
              height: 20.h,
              child: Checkbox(
                value: value,
                onChanged: enabled ? onChanged : null,
                activeColor: theme.colorScheme.primary,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(4.r),
                ),
              ),
            ),
            SizedBox(width: 12.w),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 12.sp,
                  color: enabled
                      ? theme.colorScheme.onSurface
                      : theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Campo para upload de imagem com preview.
class AppImageField extends StatelessWidget {
  final String? label;
  final String? imageUrl;
  final VoidCallback? onTap;
  final VoidCallback? onRemove;
  final IconData icon;
  final String placeholder;
  final String uploadText;
  final double size;
  final Color? iconColor;
  final Color? backgroundColor;

  const AppImageField({
    super.key,
    this.label,
    this.imageUrl,
    this.onTap,
    this.onRemove,
    this.icon = Icons.photo_camera,
    this.placeholder = 'Toque para adicionar imagem',
    this.uploadText = 'Enviar imagem',
    this.size = 80,
    this.iconColor,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final iconColorValue = iconColor ?? theme.colorScheme.primary;
    final bgColorValue = backgroundColor ?? theme.colorScheme.primary.withValues(alpha: 0.1);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null)
          Padding(
            padding: EdgeInsets.only(bottom: 8.h),
            child: Text(
              label!,
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: FontWeight.w500,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
              ),
            ),
          ),
        InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12.r),
          child: Row(
            children: [
              Container(
                width: size.w,
                height: size.h,
                decoration: BoxDecoration(
                  color: bgColorValue,
                  borderRadius: BorderRadius.circular(12.r),
                  border: Border.all(
                    color: iconColorValue.withValues(alpha: 0.3),
                    width: 1.0,
                  ),
                  image: imageUrl != null && imageUrl!.isNotEmpty
                      ? DecorationImage(
                          image: NetworkImage(imageUrl!),
                          fit: BoxFit.cover,
                        )
                      : null,
                ),
                child: imageUrl == null || imageUrl!.isEmpty
                    ? Icon(
                        icon,
                        size: size / 2.5,
                        color: iconColorValue,
                      )
                    : null,
              ),
              SizedBox(width: 16.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      imageUrl != null && imageUrl!.isNotEmpty
                          ? 'Toque para alterar imagem'
                          : placeholder,
                      style: TextStyle(
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w500,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
                    SizedBox(height: 4.h),
                    Container(
                      padding: EdgeInsets.symmetric(
                        horizontal: 12.w,
                        vertical: 6.h,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16.r),
                        border: Border.all(
                          color: theme.colorScheme.outline.withValues(alpha: 0.3),
                          width: 1.0,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.upload_file,
                            size: 14.r,
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                          ),
                          SizedBox(width: 4.w),
                          Text(
                            uploadText,
                            style: TextStyle(
                              fontSize: 12.sp,
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              if (imageUrl != null && imageUrl!.isNotEmpty && onRemove != null)
                IconButton(
                  icon: Icon(
                    Icons.delete_outline,
                    size: 20.r,
                    color: theme.colorScheme.error,
                  ),
                  onPressed: onRemove,
                ),
            ],
          ),
        ),
      ],
    );
  }
}