'use client';

import { useEffect, useState } from 'react';
import { PlusIcon, PencilIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import { subscribeToUsers, deactivateUser, reactivateUser } from '@/lib/firebase/users';
import type { User, UserRole } from '@/lib/types';
import UserForm from '@/components/admin/UserForm';

const ROLE_LABELS: Record<UserRole, string> = {
  gestor: 'Gestor',
  gerente: 'Gerente',
  barista: 'Barista',
};

const ROLE_COLORS: Record<UserRole, string> = {
  gestor: 'bg-accent/10 text-accent',
  gerente: 'bg-blue-100 text-blue-700',
  barista: 'bg-green-100 text-green-700',
};

export default function FuncionáriosPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('active');

  useEffect(() => {
    const unsubscribe = subscribeToUsers((allUsers) => {
      setUsers(allUsers);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const filteredUsers = users.filter((user) => {
    if (filter === 'active') return user.active;
    if (filter === 'inactive') return !user.active;
    return true;
  });

  const handleToggleActive = async (user: User) => {
    try {
      if (user.active) {
        await deactivateUser(user.id);
      } else {
        await reactivateUser(user.id);
      }
    } catch (error) {
      console.error('Error toggling user active status:', error);
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingUser(null);
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-gray-mid">Carregando funcionários...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary">Funcionários</h1>
          <p className="text-gray-mid">
            {filteredUsers.length} {filter === 'active' ? 'ativos' : filter === 'inactive' ? 'inativos' : 'total'}
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover"
        >
          <PlusIcon className="h-5 w-5" />
          Novo Funcionário
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(['active', 'inactive', 'all'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              filter === f
                ? 'bg-primary text-white'
                : 'bg-gray-light text-gray-dark hover:bg-gray-200'
            }`}
          >
            {f === 'active' ? 'Ativos' : f === 'inactive' ? 'Inativos' : 'Todos'}
          </button>
        ))}
      </div>

      {/* User List */}
      {filteredUsers.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
          <UserCircleIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 font-medium text-primary">Nenhum funcionário encontrado</h3>
          <p className="mt-1 text-sm text-gray-mid">
            {filter === 'active'
              ? 'Não há funcionários ativos.'
              : filter === 'inactive'
              ? 'Não há funcionários inativos.'
              : 'Adicione o primeiro funcionário.'}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredUsers.map((user) => (
            <div
              key={user.id}
              className={`rounded-xl border bg-white p-4 transition ${
                user.active ? 'border-gray-200' : 'border-gray-200 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {user.photoURL ? (
                    <img
                      src={user.photoURL}
                      alt={user.name}
                      className="h-12 w-12 rounded-full object-cover"
                    />
                  ) : (
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-light text-lg font-medium text-gray-dark">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h3 className="font-medium text-primary">{user.name}</h3>
                    <p className="text-sm text-gray-mid">{user.email}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleEdit(user)}
                  className="rounded-lg p-2 text-gray-mid hover:bg-gray-light hover:text-primary"
                >
                  <PencilIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <span className={`rounded-full px-3 py-1 text-xs font-medium ${ROLE_COLORS[user.role]}`}>
                  {ROLE_LABELS[user.role]}
                </span>
                <button
                  onClick={() => handleToggleActive(user)}
                  className={`text-sm font-medium ${
                    user.active ? 'text-red-600 hover:text-red-700' : 'text-green-600 hover:text-green-700'
                  }`}
                >
                  {user.active ? 'Desativar' : 'Reativar'}
                </button>
              </div>

              {user.lastLogin && (
                <p className="mt-3 text-xs text-gray-mid">
                  Último acesso: {new Date(user.lastLogin).toLocaleDateString('pt-BR')}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* User Form Modal */}
      {showForm && (
        <UserForm
          user={editingUser}
          onClose={handleCloseForm}
          onSuccess={handleCloseForm}
        />
      )}
    </div>
  );
}
