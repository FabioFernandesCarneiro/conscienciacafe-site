import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

/// Seção de formulário com título e conteúdo em um card.
///
/// Este componente fornece uma seção visualmente distinta para agrupar
/// campos de formulário relacionados, com um cabeçalho opcional e um
/// botão de ação opcional.
class FormSection extends StatelessWidget {
  final String? title;
  final List<Widget> children;
  final Widget? action;
  final EdgeInsetsGeometry? padding;
  final bool hasShadow;
  final Color? backgroundColor;
  final double? borderRadius;
  final Widget? icon;
  final Color? titleColor;
  final bool removePadding;

  const FormSection({
    super.key,
    this.title,
    required this.children,
    this.action,
    this.padding,
    this.hasShadow = true,
    this.backgroundColor,
    this.borderRadius,
    this.icon,
    this.titleColor,
    this.removePadding = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Container(
      margin: EdgeInsets.only(bottom: 16.h),
      decoration: BoxDecoration(
        color: backgroundColor ?? theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(borderRadius ?? 12.r),
        boxShadow: hasShadow
            ? [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 5,
                  offset: const Offset(0, 2),
                ),
              ]
            : null,
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.1),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null)
            Padding(
              padding: EdgeInsets.only(
                left: 16.w,
                right: 16.w,
                top: 16.h,
                bottom: 12.h,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      if (icon != null) ...[
                        icon!,
                        SizedBox(width: 8.w),
                      ],
                      Text(
                        title!,
                        style: TextStyle(
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w600,
                          color: titleColor ?? theme.colorScheme.onSurface,
                        ),
                      ),
                    ],
                  ),
                  if (action != null) action!,
                ],
              ),
            ),
          Padding(
            padding: removePadding
                ? EdgeInsets.zero
                : padding ??
                    EdgeInsets.all(16.r),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var i = 0; i < children.length; i++) ...[
                  children[i],
                  if (i < children.length - 1) SizedBox(height: 16.h),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Grupo de campos de formulário com título opcional.
///
/// Este componente fornece um container para agrupar campos de formulário
/// relacionados com um estilo mais leve que o FormSection. Útil para subseções
/// dentro de um FormSection.
class FormGroup extends StatelessWidget {
  final String? title;
  final List<Widget> children;
  final EdgeInsetsGeometry? padding;
  final bool hasBorder;
  final Color? backgroundColor;
  final double spacing;

  const FormGroup({
    super.key,
    this.title,
    required this.children,
    this.padding,
    this.hasBorder = false,
    this.backgroundColor,
    this.spacing = 16,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (title != null)
          Padding(
            padding: EdgeInsets.only(bottom: 8.h),
            child: Text(
              title!,
              style: TextStyle(
                fontSize: 12.sp,
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
              ),
            ),
          ),
        Container(
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(8.r),
            border: hasBorder
                ? Border.all(
                    color: theme.colorScheme.outline.withValues(alpha: 0.2),
                    width: 1,
                  )
                : null,
          ),
          padding: padding,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < children.length; i++) ...[
                children[i],
                if (i < children.length - 1) SizedBox(height: spacing.h),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

/// Cabeçalho de página de formulário com ícone, título e descrição.
class FormHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final IconData? icon;
  final Color? iconColor;
  final Color? backgroundColor;
  final VoidCallback? onBack;
  final List<Widget>? actions;
  final Widget? customTitle;

  const FormHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.icon,
    this.iconColor,
    this.backgroundColor,
    this.onBack,
    this.actions,
    this.customTitle,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final bgColor = backgroundColor ?? theme.colorScheme.surface;
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 16.h),
      decoration: BoxDecoration(
        color: bgColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 1,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (onBack != null)
                GestureDetector(
                  onTap: onBack,
                  child: Container(
                    padding: EdgeInsets.only(right: 12.w),
                    child: Icon(
                      Icons.arrow_back,
                      color: theme.colorScheme.onSurface,
                      size: 24.r,
                    ),
                  ),
                ),
              if (icon != null) ...[
                Container(
                  width: 40.r,
                  height: 40.r,
                  decoration: BoxDecoration(
                    color: (iconColor ?? theme.colorScheme.primary).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8.r),
                  ),
                  child: Icon(
                    icon,
                    color: iconColor ?? theme.colorScheme.primary,
                    size: 20.r,
                  ),
                ),
                SizedBox(width: 12.w),
              ],
              Expanded(
                child: customTitle ??
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.onSurface,
                      ),
                    ),
              ),
              if (actions != null && actions!.isNotEmpty) ...actions!,
            ],
          ),
          if (subtitle != null) ...[
            SizedBox(height: 4.h),
            Padding(
              padding: EdgeInsets.only(left: icon != null ? 52.w : 0),
              child: Text(
                subtitle!,
                style: TextStyle(
                  fontSize: 12.sp,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Box de informação ou dica para o usuário.
class FormInfoTip extends StatelessWidget {
  final String message;
  final InfoType type;
  final IconData? icon;

  const FormInfoTip({
    super.key,
    required this.message,
    this.type = InfoType.info,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    // Definir cores e ícones com base no tipo
    late final Color backgroundColor;
    late final Color textColor;
    late final IconData iconData;
    
    switch (type) {
      case InfoType.info:
        backgroundColor = theme.colorScheme.primary.withValues(alpha: 0.1);
        textColor = theme.colorScheme.primary;
        iconData = icon ?? Icons.info_outline;
        break;
      case InfoType.success:
        backgroundColor = Colors.green.withValues(alpha: 0.1);
        textColor = Colors.green;
        iconData = icon ?? Icons.check_circle_outline;
        break;
      case InfoType.warning:
        backgroundColor = Colors.orange.withValues(alpha: 0.1);
        textColor = Colors.orange;
        iconData = icon ?? Icons.warning_amber_outlined;
        break;
      case InfoType.error:
        backgroundColor = theme.colorScheme.error.withValues(alpha: 0.1);
        textColor = theme.colorScheme.error;
        iconData = icon ?? Icons.error_outline;
        break;
    }
    
    return Container(
      padding: EdgeInsets.all(12.r),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            iconData,
            color: textColor,
            size: 18.r,
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                fontSize: 12.sp,
                color: textColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Tipos de informação para o FormInfoTip
enum InfoType {
  info,
  success,
  warning,
  error,
}

/// Elemento separador com linha e texto opcional.
class FormDivider extends StatelessWidget {
  final String? text;
  final Color? color;
  final double thickness;
  final double indent;
  final double endIndent;

  const FormDivider({
    super.key,
    this.text,
    this.color,
    this.thickness = 1,
    this.indent = 0,
    this.endIndent = 0,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final lineColor = color ?? theme.colorScheme.outline.withValues(alpha: 0.2);
    
    if (text == null) {
      return Divider(
        color: lineColor,
        thickness: thickness,
        indent: indent,
        endIndent: endIndent,
        height: 24.h,
      );
    }
    
    return Row(
      children: [
        Expanded(
          child: Container(
            margin: EdgeInsets.only(left: indent, right: 16.w),
            height: thickness,
            color: lineColor,
          ),
        ),
        Text(
          text!,
          style: TextStyle(
            fontSize: 12.sp,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
            fontWeight: FontWeight.w500,
          ),
        ),
        Expanded(
          child: Container(
            margin: EdgeInsets.only(left: 16.w, right: endIndent),
            height: thickness,
            color: lineColor,
          ),
        ),
      ],
    );
  }
}

/// Grid para campos de formulário.
class FormGrid extends StatelessWidget {
  final List<Widget> children;
  final int columns;
  final double spacing;
  final double runSpacing;

  const FormGrid({
    super.key,
    required this.children,
    this.columns = 2,
    this.spacing = 16,
    this.runSpacing = 16,
  });

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: columns,
        crossAxisSpacing: spacing.w,
        mainAxisSpacing: runSpacing.h,
        mainAxisExtent: 80.h, // Ajuste conforme necessário
      ),
      itemCount: children.length,
      itemBuilder: (context, index) => children[index],
    );
  }
}

/// Componente de tags interativas para seleção múltipla.
class TagsSelector extends StatelessWidget {
  final List<String> options;
  final List<String> selectedOptions;
  final Function(List<String>) onChanged;
  final String? label;
  final bool showAddButton;
  final VoidCallback? onAddPressed;
  final Color? tagColor;
  final String? placeholder;

  const TagsSelector({
    super.key,
    required this.options,
    required this.selectedOptions,
    required this.onChanged,
    this.label,
    this.showAddButton = false,
    this.onAddPressed,
    this.tagColor,
    this.placeholder,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tagColorValue = tagColor ?? theme.colorScheme.primary;
    
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
        Wrap(
          spacing: 8.w,
          runSpacing: 8.h,
          children: [
            ...options.map((option) {
              final isSelected = selectedOptions.contains(option);
              return GestureDetector(
                onTap: () {
                  final newSelection = List<String>.from(selectedOptions);
                  if (isSelected) {
                    newSelection.remove(option);
                  } else {
                    newSelection.add(option);
                  }
                  onChanged(newSelection);
                },
                child: Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: 12.w,
                    vertical: 6.h,
                  ),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? tagColorValue.withValues(alpha: 0.1)
                        : theme.colorScheme.surface,
                    borderRadius: BorderRadius.circular(16.r),
                    border: Border.all(
                      color: isSelected
                          ? tagColorValue
                          : theme.colorScheme.outline.withValues(alpha: 0.3),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        option,
                        style: TextStyle(
                          fontSize: 12.sp,
                          color: isSelected
                              ? tagColorValue
                              : theme.colorScheme.onSurface,
                        ),
                      ),
                      if (isSelected) ...[
                        SizedBox(width: 4.w),
                        Icon(
                          Icons.check,
                          size: 16.r,
                          color: tagColorValue,
                        ),
                      ],
                    ],
                  ),
                ),
              );
            }),
            if (showAddButton)
              GestureDetector(
                onTap: onAddPressed,
                child: Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: 12.w,
                    vertical: 6.h,
                  ),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surface,
                    borderRadius: BorderRadius.circular(16.r),
                    border: Border.all(
                      color: theme.colorScheme.primary.withValues(alpha: 0.3),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.add,
                        size: 16.r,
                        color: theme.colorScheme.primary,
                      ),
                      SizedBox(width: 4.w),
                      Text(
                        'Adicionar',
                        style: TextStyle(
                          fontSize: 12.sp,
                          color: theme.colorScheme.primary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
        if (options.isEmpty && placeholder != null)
          Text(
            placeholder!,
            style: TextStyle(
              fontSize: 12.sp,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
              fontStyle: FontStyle.italic,
            ),
          ),
      ],
    );
  }
}

/// Barra de ações fixa na parte inferior do formulário.
class FormBottomBar extends StatelessWidget {
  final Widget primaryButton;
  final Widget? secondaryButton;
  final bool hasShadow;
  final Color? backgroundColor;
  final EdgeInsetsGeometry? padding;

  const FormBottomBar({
    super.key,
    required this.primaryButton,
    this.secondaryButton,
    this.hasShadow = true,
    this.backgroundColor,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Container(
      padding: padding ?? EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: backgroundColor ?? theme.colorScheme.surface,
        boxShadow: hasShadow
            ? [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.1),
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ]
            : null,
        border: hasShadow
            ? null
            : Border(
                top: BorderSide(
                  color: theme.colorScheme.outline.withValues(alpha: 0.1),
                  width: 1,
                ),
              ),
      ),
      child: SafeArea(
        top: false,
        child: secondaryButton != null
            ? Row(
                children: [
                  Expanded(child: secondaryButton!),
                  SizedBox(width: 12.w),
                  Expanded(child: primaryButton),
                ],
              )
            : primaryButton,
      ),
    );
  }
}

/// Mixin para adicionar padding de bottom bar a uma tela de formulário.
mixin FormScreenPadding {
  Widget withBottomPadding(Widget child) {
    return Column(
      children: [
        Expanded(child: child),
        SizedBox(height: 80.h), // Espaço para a barra inferior
      ],
    );
  }
}