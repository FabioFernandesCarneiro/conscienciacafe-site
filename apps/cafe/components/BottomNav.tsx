'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  HomeIcon,
  ClipboardDocumentListIcon,
  BanknotesIcon,
  UsersIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  ClipboardDocumentListIcon as ClipboardIconSolid,
  BanknotesIcon as BanknotesIconSolid,
  UsersIcon as UsersIconSolid,
  Cog6ToothIcon as CogIconSolid,
} from '@heroicons/react/24/solid';
import { useAuth } from '@/lib/hooks/useAuth';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  activeIcon: React.ElementType;
  roles?: ('gestor' | 'gerente' | 'barista')[];
}

const navItems: NavItem[] = [
  {
    name: 'Pedidos',
    href: '/',
    icon: ClipboardDocumentListIcon,
    activeIcon: ClipboardIconSolid,
    roles: ['gestor', 'gerente', 'barista'],
  },
  {
    name: 'Caixa',
    href: '/caixa',
    icon: BanknotesIcon,
    activeIcon: BanknotesIconSolid,
    roles: ['gestor', 'gerente'],
  },
  {
    name: 'Clientes',
    href: '/clientes',
    icon: UsersIcon,
    activeIcon: UsersIconSolid,
    roles: ['gestor', 'gerente'],
  },
  {
    name: 'Admin',
    href: '/admin',
    icon: Cog6ToothIcon,
    activeIcon: CogIconSolid,
    roles: ['gestor'],
  },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { user, hasRole } = useAuth();

  // Filter items based on user role
  const visibleItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return item.roles.some((role) => hasRole(role));
  });

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/' || pathname === '/pedido';
    }
    return pathname?.startsWith(href);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white pb-safe lg:hidden">
      <div className="flex items-center justify-around">
        {visibleItems.map((item) => {
          const active = isActive(item.href);
          const Icon = active ? item.activeIcon : item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex flex-1 flex-col items-center gap-1 py-3 transition ${
                active ? 'text-accent' : 'text-gray-mid'
              }`}
            >
              <Icon className="h-6 w-6" />
              <span className="text-xs font-medium">{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
