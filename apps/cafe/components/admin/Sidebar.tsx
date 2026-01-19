'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  HomeIcon,
  UsersIcon,
  CubeIcon,
  Cog6ToothIcon,
  ArrowLeftOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';
import { useAuth } from '@/lib/hooks/useAuth';

const navItems = [
  { name: 'Dashboard', href: '/admin', icon: HomeIcon },
  { name: 'Funcionários', href: '/admin/funcionarios', icon: UsersIcon },
  { name: 'Produtos', href: '/admin/produtos', icon: CubeIcon },
  { name: 'Configurações', href: '/admin/configuracoes', icon: Cog6ToothIcon },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === '/admin') {
      return pathname === '/admin' || pathname === '/admin/';
    }
    return pathname?.startsWith(href);
  };

  const handleSignOut = async () => {
    await signOut();
    window.location.href = '/login';
  };

  const NavContent = () => (
    <>
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
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                active
                  ? 'bg-accent text-white'
                  : 'text-gray-dark hover:bg-gray-light'
              }`}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="border-t border-gray-200 p-4">
        <div className="mb-3 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-light text-sm font-medium text-gray-dark">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-primary">
              {user?.name || 'Usuario'}
            </p>
            <p className="truncate text-xs text-gray-mid capitalize">
              {user?.role || 'barista'}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Link
            href="/"
            className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-dark hover:bg-gray-light"
          >
            <HomeIcon className="h-4 w-4" />
            App
          </Link>
          <button
            onClick={handleSignOut}
            className="flex items-center justify-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-dark hover:bg-gray-light"
          >
            <ArrowLeftOnRectangleIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-4 z-40 rounded-lg bg-white p-2 shadow-lg lg:hidden"
      >
        <Bars3Icon className="h-6 w-6 text-primary" />
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform bg-white shadow-xl transition-transform lg:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute right-4 top-4"
        >
          <XMarkIcon className="h-6 w-6 text-gray-mid" />
        </button>
        <div className="flex h-full flex-col">
          <NavContent />
        </div>
      </aside>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-gray-200 lg:bg-white">
        <NavContent />
      </aside>
    </>
  );
}
