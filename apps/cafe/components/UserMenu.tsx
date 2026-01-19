'use client';

import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { useRouter } from 'next/navigation';
import {
  ChevronDownIcon,
  KeyIcon,
  ArrowLeftStartOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '@/lib/hooks/useAuth';

interface UserMenuProps {
  showName?: boolean;
  compact?: boolean;
}

export default function UserMenu({ showName = true, compact = false }: UserMenuProps) {
  const router = useRouter();
  const { user, signOut, isEmailPasswordUser } = useAuth();

  const handleSignOut = async () => {
    await signOut();
    router.push('/login');
  };

  const handleChangePassword = () => {
    router.push('/trocar-senha');
  };

  if (!user) return null;

  const initials = user.name
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const firstName = user.name.split(' ')[0];

  return (
    <Menu as="div" className="relative">
      <Menu.Button
        className={`flex items-center gap-2 rounded-lg transition hover:bg-gray-light ${
          compact ? 'p-1' : 'px-2 py-1.5'
        }`}
      >
        {/* Avatar */}
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 text-sm font-medium text-gray-dark">
          {user.photoURL ? (
            <img
              src={user.photoURL}
              alt={user.name}
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            initials
          )}
        </div>

        {/* Name (optional) */}
        {showName && (
          <span className="hidden text-sm text-gray-dark sm:block">
            Ola, {firstName}
          </span>
        )}

        <ChevronDownIcon className="h-4 w-4 text-gray-mid" />
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-xl bg-white shadow-lg ring-1 ring-black/5 focus:outline-none">
          {/* User Info */}
          <div className="border-b border-gray-100 px-4 py-3">
            <p className="text-sm font-medium text-primary">{user.name}</p>
            <p className="text-xs text-gray-mid capitalize">{user.role}</p>
          </div>

          <div className="p-1">
            {/* Change Password (only for email/password users) */}
            {isEmailPasswordUser && (
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={handleChangePassword}
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                      active ? 'bg-gray-light text-primary' : 'text-gray-dark'
                    }`}
                  >
                    <KeyIcon className="h-5 w-5" />
                    Trocar Senha
                  </button>
                )}
              </Menu.Item>
            )}

            {/* Sign Out */}
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={handleSignOut}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                    active ? 'bg-gray-light text-primary' : 'text-gray-dark'
                  }`}
                >
                  <ArrowLeftStartOnRectangleIcon className="h-5 w-5" />
                  Sair
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
}
