import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class AppBottomNavigation extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;
  final List<BottomNavigationItem> items;
  final Color activeColor;

  const AppBottomNavigation({
    super.key,
    required this.currentIndex,
    required this.onTap,
    required this.items,
    required this.activeColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return BottomNavigationBar(
      currentIndex: currentIndex,
      onTap: onTap,
      type: BottomNavigationBarType.fixed,
      backgroundColor: Colors.white,
      selectedItemColor: activeColor,
      unselectedItemColor: theme.colorScheme.onSurface.withValues(alpha: 0.6),
      selectedLabelStyle: theme.textTheme.titleMedium?.copyWith(
        fontSize: 10.sp,
      ),
      unselectedLabelStyle: theme.textTheme.titleMedium?.copyWith(
        fontSize: 10.sp,
        color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
      ),
      items: items.map((item) => item.toBottomNavigationBarItem()).toList(),
    );
  }
}

class BottomNavigationItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;

  const BottomNavigationItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });

  BottomNavigationBarItem toBottomNavigationBarItem() {
    return BottomNavigationBarItem(
      icon: Icon(icon),
      activeIcon: Icon(activeIcon),
      label: label,
    );
  }
}