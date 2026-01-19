'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { UsersIcon, CubeIcon, ShoppingCartIcon } from '@heroicons/react/24/outline';
import { subscribeToUsers } from '@/lib/firebase/users';
import { subscribeToProducts } from '@/lib/firebase/products';
import type { User, Product } from '@/lib/types';

interface DashboardStats {
  totalUsers: number;
  activeUsers: number;
  totalProducts: number;
  activeProducts: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalUsers: 0,
    activeUsers: 0,
    totalProducts: 0,
    activeProducts: 0,
  });

  useEffect(() => {
    const unsubUsers = subscribeToUsers((users: User[]) => {
      setStats((prev) => ({
        ...prev,
        totalUsers: users.length,
        activeUsers: users.filter((u) => u.active).length,
      }));
    });

    const unsubProducts = subscribeToProducts((products: Product[]) => {
      setStats((prev) => ({
        ...prev,
        totalProducts: products.length,
        activeProducts: products.filter((p) => p.active).length,
      }));
    }, true); // includeInactive = true for admin stats

    return () => {
      unsubUsers();
      unsubProducts();
    };
  }, []);

  const cards = [
    {
      title: 'Funcionários',
      description: 'Gerenciar equipe',
      href: '/admin/funcionarios',
      icon: UsersIcon,
      stat: `${stats.activeUsers}/${stats.totalUsers} ativos`,
    },
    {
      title: 'Produtos',
      description: 'Cardápio e preços',
      href: '/admin/produtos',
      icon: CubeIcon,
      stat: `${stats.activeProducts}/${stats.totalProducts} ativos`,
    },
    {
      title: 'Pedidos',
      description: 'Ver histórico',
      href: '/',
      icon: ShoppingCartIcon,
      stat: 'Acompanhar pedidos',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-primary">Dashboard</h1>
        <p className="text-gray-mid">Gerenciamento do Consciência Café</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <Link
            key={card.title}
            href={card.href}
            className="group rounded-xl border border-gray-200 bg-white p-6 transition hover:border-accent hover:shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div className="rounded-lg bg-gray-light p-3 group-hover:bg-accent/10">
                <card.icon className="h-6 w-6 text-gray-dark group-hover:text-accent" />
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-lg font-bold text-primary">{card.title}</h3>
              <p className="text-sm text-gray-mid">{card.description}</p>
            </div>
            <div className="mt-4 text-sm font-medium text-accent">{card.stat}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
