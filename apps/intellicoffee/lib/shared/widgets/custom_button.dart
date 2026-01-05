import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final Color? backgroundColor;
  final Color? textColor;
  final bool isOutlined;
  final bool isLoading;
  final double? width;
  final double? height;
  final IconData? icon;
  final bool isDisabled;

  const CustomButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.backgroundColor,
    this.textColor,
    this.isOutlined = false,
    this.isLoading = false,
    this.width,
    this.height,
    this.icon,
    this.isDisabled = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final buttonColor = backgroundColor ?? theme.colorScheme.primary;
    
    return SizedBox(
      width: width,
      height: height ?? 48.h,
      child: isOutlined 
        ? OutlinedButton(
            onPressed: isDisabled || isLoading ? null : onPressed,
            style: OutlinedButton.styleFrom(
              side: BorderSide(color: buttonColor),
              foregroundColor: textColor ?? buttonColor,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8.r),
              ),
            ),
            child: _buildChild(theme, true),
          )
        : ElevatedButton(
            onPressed: isDisabled || isLoading ? null : onPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: buttonColor,
              foregroundColor: textColor ?? Colors.white,
              disabledBackgroundColor: theme.colorScheme.surfaceContainerHighest,
              disabledForegroundColor: theme.colorScheme.onSurfaceVariant,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8.r),
              ),
            ),
            child: _buildChild(theme, false),
          ),
    );
  }

  Widget _buildChild(ThemeData theme, bool isOutlined) {
    if (isLoading) {
      return SizedBox(
        width: 24.r,
        height: 24.r,
        child: CircularProgressIndicator(
          strokeWidth: 2,
          valueColor: AlwaysStoppedAnimation<Color>(
            isOutlined ? (backgroundColor ?? theme.colorScheme.primary) : Colors.white,
          ),
        ),
      );
    }

    if (icon != null) {
      return Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 18.sp),
          SizedBox(width: 8.w),
          Text(
            text,
            style: TextStyle(
              fontSize: 12.sp,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      );
    }

    return Text(
      text,
      style: TextStyle(
        fontSize: 12.sp,
        fontWeight: FontWeight.w500,
      ),
    );
  }
} 