import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

/// Botão padrão com estilo consistente para o IntelliCoffee.
///
/// Este widget fornece um botão com aparência padronizada, respeitando
/// o design system da aplicação.
class FormButton extends StatelessWidget {
  final String? label;
  final Widget? child;
  final VoidCallback? onPressed;
  final ButtonType type;
  final bool isLoading;
  final bool isFullWidth;
  final EdgeInsetsGeometry? padding;
  final double? height;
  final IconData? icon;
  final Color? backgroundColor;
  final Color? textColor;
  final double? fontSize;
  final double? borderRadius;
  final Widget? prefix;
  final Widget? suffix;

  const FormButton({
    super.key,
    this.label,
    this.child,
    this.onPressed,
    this.type = ButtonType.primary,
    this.isLoading = false,
    this.isFullWidth = true,
    this.padding,
    this.height,
    this.icon,
    this.backgroundColor,
    this.textColor,
    this.fontSize,
    this.borderRadius,
    this.prefix,
    this.suffix,
  })  : assert(label != null || child != null,
            'Either label or child must be provided');

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    // Definir cores com base no tipo
    Color bgColor;
    Color txtColor;
    Color borderColor;
    
    switch (type) {
      case ButtonType.primary:
        bgColor = backgroundColor ?? theme.colorScheme.primary;
        txtColor = textColor ?? theme.colorScheme.onPrimary;
        borderColor = backgroundColor ?? theme.colorScheme.primary;
        break;
      case ButtonType.secondary:
        bgColor = Colors.transparent;
        txtColor = backgroundColor ?? theme.colorScheme.primary;
        borderColor = backgroundColor ?? theme.colorScheme.primary;
        break;
      case ButtonType.text:
        bgColor = Colors.transparent;
        txtColor = backgroundColor ?? theme.colorScheme.primary;
        borderColor = Colors.transparent;
        break;
      case ButtonType.error:
        bgColor = backgroundColor ?? theme.colorScheme.error;
        txtColor = textColor ?? theme.colorScheme.onError;
        borderColor = backgroundColor ?? theme.colorScheme.error;
        break;
    }
    
    // Widget de conteúdo do botão
    Widget buttonContent;
    if (isLoading) {
      buttonContent = SizedBox(
        height: 20.h,
        width: 20.w,
        child: CircularProgressIndicator(
          strokeWidth: 2.0,
          valueColor: AlwaysStoppedAnimation<Color>(txtColor),
        ),
      );
    } else if (child != null) {
      buttonContent = child!;
    } else {
      buttonContent = Row(
        mainAxisSize: isFullWidth ? MainAxisSize.max : MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (prefix != null) ...[
            prefix!,
            SizedBox(width: 8.w),
          ],
          if (icon != null) ...[
            Icon(
              icon,
              size: 18.r,
              color: txtColor,
            ),
            SizedBox(width: 8.w),
          ],
          Flexible(
            child: Text(
              label!,
              style: TextStyle(
                color: txtColor,
                fontSize: fontSize ?? 12.sp,
                fontWeight: FontWeight.w500,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (suffix != null) ...[
            SizedBox(width: 8.w),
            suffix!,
          ],
        ],
      );
    }
    
    // Estilo do botão com base no tipo
    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(borderRadius ?? 8.r),
      child: InkWell(
        onTap: isLoading ? null : onPressed,
        borderRadius: BorderRadius.circular(borderRadius ?? 8.r),
        child: Ink(
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.circular(borderRadius ?? 8.r),
            border: type == ButtonType.secondary
                ? Border.all(color: borderColor, width: 1.5)
                : type == ButtonType.text
                    ? null
                    : Border.all(color: borderColor, width: 0),
          ),
          child: Container(
            height: height ?? 48.h,
            padding: padding ??
                EdgeInsets.symmetric(horizontal: 20.w, vertical: 0),
            width: isFullWidth ? double.infinity : null,
            alignment: Alignment.center,
            child: buttonContent,
          ),
        ),
      ),
    );
  }
}

/// Tipos de botão disponíveis
enum ButtonType {
  primary,
  secondary,
  text,
  error,
}

/// Botão primário (cor de destaque com texto branco)
class PrimaryButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isFullWidth;
  final IconData? icon;
  final Color? backgroundColor;
  final EdgeInsetsGeometry? padding;
  final double? height;

  const PrimaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.isLoading = false,
    this.isFullWidth = true,
    this.icon,
    this.backgroundColor,
    this.padding,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return FormButton(
      label: label,
      onPressed: onPressed,
      type: ButtonType.primary,
      isLoading: isLoading,
      isFullWidth: isFullWidth,
      icon: icon,
      backgroundColor: backgroundColor,
      padding: padding,
      height: height,
    );
  }
}

/// Botão secundário (borda colorida com texto colorido)
class SecondaryButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isFullWidth;
  final IconData? icon;
  final Color? color;
  final EdgeInsetsGeometry? padding;
  final double? height;

  const SecondaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.isLoading = false,
    this.isFullWidth = true,
    this.icon,
    this.color,
    this.padding,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return FormButton(
      label: label,
      onPressed: onPressed,
      type: ButtonType.secondary,
      isLoading: isLoading,
      isFullWidth: isFullWidth,
      icon: icon,
      backgroundColor: color,
      padding: padding,
      height: height,
    );
  }
}

/// Botão de texto (sem fundo ou borda)
class TextButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final IconData? icon;
  final Color? color;
  final double? fontSize;

  const TextButton({
    super.key,
    required this.label,
    this.onPressed,
    this.isLoading = false,
    this.icon,
    this.color,
    this.fontSize,
  });

  @override
  Widget build(BuildContext context) {
    return FormButton(
      label: label,
      onPressed: onPressed,
      type: ButtonType.text,
      isLoading: isLoading,
      isFullWidth: false,
      icon: icon,
      backgroundColor: color,
      fontSize: fontSize ?? 12.sp,
      height: 32.h,
      padding: EdgeInsets.symmetric(horizontal: 12.w),
    );
  }
}

/// Botão de ícone circular (para ações como adicionar ou remover)
class IconActionButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;
  final Color? backgroundColor;
  final Color? iconColor;
  final double size;
  final double? iconSize;
  final Widget? badge;
  final String? tooltip;

  const IconActionButton({
    super.key,
    required this.icon,
    this.onPressed,
    this.backgroundColor,
    this.iconColor,
    this.size = 40,
    this.iconSize,
    this.badge,
    this.tooltip,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    final button = Stack(
      clipBehavior: Clip.none,
      children: [
        Material(
          color: backgroundColor ?? theme.colorScheme.primary.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(size / 2),
          child: InkWell(
            onTap: onPressed,
            borderRadius: BorderRadius.circular(size / 2),
            child: Container(
              width: size.r,
              height: size.r,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
              ),
              child: Icon(
                icon,
                size: iconSize ?? size / 2,
                color: iconColor ?? theme.colorScheme.primary,
              ),
            ),
          ),
        ),
        if (badge != null)
          Positioned(
            top: -5.r,
            right: -5.r,
            child: badge!,
          ),
      ],
    );
    
    if (tooltip != null) {
      return Tooltip(
        message: tooltip!,
        child: button,
      );
    }
    
    return button;
  }
}

/// Botão flutuante de ação (FAB)
class ActionButton extends StatelessWidget {
  final String? label;
  final IconData icon;
  final VoidCallback? onPressed;
  final bool extended;
  final Color? backgroundColor;
  final Color? iconColor;
  final double? size;

  const ActionButton({
    super.key,
    this.label,
    required this.icon,
    this.onPressed,
    this.extended = false,
    this.backgroundColor,
    this.iconColor,
    this.size,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    if (extended && label != null) {
      return FloatingActionButton.extended(
        onPressed: onPressed,
        backgroundColor: backgroundColor ?? theme.colorScheme.primary,
        icon: Icon(
          icon,
          color: iconColor ?? theme.colorScheme.onPrimary,
        ),
        label: Text(
          label!,
          style: TextStyle(
            color: iconColor ?? theme.colorScheme.onPrimary,
            fontWeight: FontWeight.w500,
          ),
        ),
      );
    }
    
    return FloatingActionButton(
      onPressed: onPressed,
      mini: size != null && size! < 50,
      backgroundColor: backgroundColor ?? theme.colorScheme.primary,
      child: Icon(
        icon,
        color: iconColor ?? theme.colorScheme.onPrimary,
        size: size != null ? size! / 2 : 24.r,
      ),
    );
  }
}

/// Badge para botões de notificação
class NotificationBadge extends StatelessWidget {
  final int count;
  final Color? backgroundColor;
  final Color? textColor;

  const NotificationBadge({
    super.key,
    required this.count,
    this.backgroundColor,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    if (count <= 0) {
      return const SizedBox.shrink();
    }
    
    return Container(
      padding: EdgeInsets.all(4.r),
      decoration: BoxDecoration(
        color: backgroundColor ?? theme.colorScheme.error,
        shape: BoxShape.circle,
      ),
      constraints: BoxConstraints(
        minWidth: 16.r,
        minHeight: 16.r,
      ),
      child: Center(
        child: Text(
          count > 9 ? '9+' : count.toString(),
          style: TextStyle(
            color: textColor ?? theme.colorScheme.onError,
            fontSize: 10.sp,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}

/// Botão com contador numérico integrado
class CounterButton extends StatelessWidget {
  final int value;
  final ValueChanged<int>? onChanged;
  final int min;
  final int max;
  final double size;
  final Color? backgroundColor;
  final Color? textColor;
  final bool enabled;

  const CounterButton({
    super.key,
    required this.value,
    this.onChanged,
    this.min = 0,
    this.max = 999,
    this.size = 36,
    this.backgroundColor,
    this.textColor,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final bgColor = backgroundColor ?? theme.colorScheme.primary;
    final txtColor = textColor ?? theme.colorScheme.onPrimary;
    
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconActionButton(
          icon: Icons.remove,
          size: size,
          backgroundColor: enabled && value > min
              ? bgColor.withValues(alpha: 0.1)
              : theme.colorScheme.onSurface.withValues(alpha: 0.05),
          iconColor: enabled && value > min
              ? bgColor
              : theme.colorScheme.onSurface.withValues(alpha: 0.3),
          onPressed: enabled && value > min
              ? () {
                  if (onChanged != null) {
                    onChanged!(value - 1);
                  }
                }
              : null,
        ),
        Container(
          width: size.r,
          height: size.r,
          margin: EdgeInsets.symmetric(horizontal: 8.w),
          decoration: BoxDecoration(
            color: bgColor,
            shape: BoxShape.circle,
          ),
          alignment: Alignment.center,
          child: Text(
            value.toString(),
            style: TextStyle(
              color: txtColor,
              fontSize: 14.sp,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        IconActionButton(
          icon: Icons.add,
          size: size,
          backgroundColor: enabled && value < max
              ? bgColor.withValues(alpha: 0.1)
              : theme.colorScheme.onSurface.withValues(alpha: 0.05),
          iconColor: enabled && value < max
              ? bgColor
              : theme.colorScheme.onSurface.withValues(alpha: 0.3),
          onPressed: enabled && value < max
              ? () {
                  if (onChanged != null) {
                    onChanged!(value + 1);
                  }
                }
              : null,
        ),
      ],
    );
  }
}

/// Botão para opção de filtro ou chip de seleção
class FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback? onPressed;
  final IconData? icon;
  final Color? selectedColor;
  final Color? unselectedColor;
  final bool showCheckmark;

  const FilterChip({
    super.key,
    required this.label,
    this.isSelected = false,
    this.onPressed,
    this.icon,
    this.selectedColor,
    this.unselectedColor,
    this.showCheckmark = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final activeColor = selectedColor ?? theme.colorScheme.primary;
    final inactiveColor = unselectedColor ?? theme.colorScheme.surface;
    
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Ink(
          decoration: BoxDecoration(
            color: isSelected
                ? activeColor.withValues(alpha: 0.1)
                : inactiveColor,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(
              color: isSelected
                  ? activeColor
                  : theme.colorScheme.outline.withValues(alpha: 0.3),
              width: 1,
            ),
          ),
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: icon != null ? 6.h : 8.h),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (icon != null) ...[
                  Icon(
                    icon,
                    size: 16.r,
                    color: isSelected
                        ? activeColor
                        : theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                  SizedBox(width: 4.w),
                ],
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 14.sp,
                    color: isSelected
                        ? activeColor
                        : theme.colorScheme.onSurface,
                  ),
                ),
                if (isSelected && showCheckmark) ...[
                  SizedBox(width: 4.w),
                  Icon(
                    Icons.check,
                    size: 16.r,
                    color: activeColor,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Grupo de botões na horizontal
class ButtonGroup extends StatelessWidget {
  final List<Widget> children;
  final double spacing;
  final MainAxisAlignment alignment;

  const ButtonGroup({
    super.key,
    required this.children,
    this.spacing = 12,
    this.alignment = MainAxisAlignment.center,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: alignment,
      children: [
        for (int i = 0; i < children.length; i++) ...[
          children[i],
          if (i < children.length - 1) SizedBox(width: spacing.w),
        ],
      ],
    );
  }
}

/// Grupo de botões na vertical
class VerticalButtonGroup extends StatelessWidget {
  final List<Widget> children;
  final double spacing;
  final CrossAxisAlignment alignment;

  const VerticalButtonGroup({
    super.key,
    required this.children,
    this.spacing = 12,
    this.alignment = CrossAxisAlignment.center,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: alignment,
      children: [
        for (int i = 0; i < children.length; i++) ...[
          children[i],
          if (i < children.length - 1) SizedBox(height: spacing.h),
        ],
      ],
    );
  }
}