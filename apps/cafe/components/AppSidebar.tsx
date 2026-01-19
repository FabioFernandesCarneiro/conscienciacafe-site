'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  ClipboardDocumentListIcon,
  BanknotesIcon,
  UsersIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import {
  ClipboardDocumentListIcon as ClipboardIconSolid,
  BanknotesIcon as BanknotesIconSolid,
  UsersIcon as UsersIconSolid,
  Cog6ToothIcon as CogIconSolid,
} from '@heroicons/react/24/solid';
import { useAuth } from '@/lib/hooks/useAuth';
import UserMenu from './UserMenu';

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

export default function AppSidebar() {
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
    <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-gray-200 lg:bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center border-b border-gray-200 px-4">
        <Image
          src="/images/logo.png"
          alt="Consciência Café"
          width={160}
          height={50}
          className="h-10 w-auto"
          unoptimized
        />
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {visibleItems.map((item) => {
          const active = isActive(item.href);
          const Icon = active ? item.activeIcon : item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                active
                  ? 'bg-accent text-white'
                  : 'text-gray-dark hover:bg-gray-light'
              }`}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <UserMenu showName={false} compact />
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-primary">
              {user?.name || 'Usuario'}
            </p>
            <p className="truncate text-xs text-gray-mid capitalize">
              {user?.role || 'barista'}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
