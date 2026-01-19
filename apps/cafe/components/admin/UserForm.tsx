'use client';

import { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { createUser, updateUser, getUserByEmail } from '@/lib/firebase/users';
import { useAuth } from '@/lib/hooks/useAuth';
import type { User, UserRole } from '@/lib/types';

interface UserFormProps {
  user?: User | null;
  onClose: () => void;
  onSuccess: () => void;
}

const ROLES: { value: UserRole; label: string; description: string }[] = [
  { value: 'barista', label: 'Barista', description: 'Apenas pedidos' },
  { value: 'gerente', label: 'Gerente', description: 'Pedidos, caixa e clientes' },
  { value: 'gestor', label: 'Gestor', description: 'Acesso total ao sistema' },
];

export default function UserForm({ user, onClose, onSuccess }: UserFormProps) {
  const { user: currentUser } = useAuth();
  const isEditing = !!user;

  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    role: user?.role || 'barista' as UserRole,
    active: user?.active ?? true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isEditing && user) {
        // Update existing user
        await updateUser(user.id, {
          name: formData.name,
          role: formData.role,
          active: formData.active,
        });
      } else {
        // Check if email already exists
        const existingUser = await getUserByEmail(formData.email);
        if (existingUser) {
          setError('Já existe um usuário com este email.');
          setLoading(false);
          return;
        }

        // Create new user profile (pre-registration)
        // The user will need to login with Google to activate their Firebase Auth account
        // We use email as temporary ID - it will be updated when they login with Google
        const tempId = `pending_${Date.now()}_${Math.random().toString(36).substring(7)}`;

        await createUser(tempId, {
          email: formData.email.toLowerCase(),
          name: formData.name,
          role: formData.role,
          active: formData.active,
          createdAt: new Date().toISOString(),
          createdBy: currentUser?.id || 'unknown',
        });
      }

      onSuccess();
    } catch (err) {
      console.error('Error saving user:', err);
      setError('Erro ao salvar usuário. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Transition appear show={true} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform rounded-2xl bg-white p-6 shadow-xl transition-all">
                <div className="flex items-center justify-between">
                  <Dialog.Title className="text-xl font-bold text-primary">
                    {isEditing ? 'Editar Funcionário' : 'Novo Funcionário'}
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="rounded-lg p-2 text-gray-mid hover:bg-gray-light hover:text-primary"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                {!isEditing && (
                  <p className="mt-2 text-sm text-gray-mid">
                    O funcionário devera fazer login com Google usando este email para ativar a conta.
                  </p>
                )}

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                  {/* Name */}
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-dark">
                      Nome completo
                    </label>
                    <input
                      type="text"
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                      placeholder="Nome do funcionário"
                      required
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-dark">
                      Email
                    </label>
                    <input
                      type="email"
                      id="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      disabled={isEditing}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-primary placeholder-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:bg-gray-light disabled:text-gray-mid"
                      placeholder="email@exemplo.com"
                      required
                    />
                    {isEditing && (
                      <p className="mt-1 text-xs text-gray-mid">Email não pode ser alterado</p>
                    )}
                  </div>

                  {/* Role */}
                  <div>
                    <label className="block text-sm font-medium text-gray-dark">Perfil</label>
                    <div className="mt-2 space-y-2">
                      {ROLES.map((role) => (
                        <label
                          key={role.value}
                          className={`flex cursor-pointer items-center rounded-lg border p-3 transition ${
                            formData.role === role.value
                              ? 'border-accent bg-accent/5'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="radio"
                            name="role"
                            value={role.value}
                            checked={formData.role === role.value}
                            onChange={(e) =>
                              setFormData({ ...formData, role: e.target.value as UserRole })
                            }
                            className="sr-only"
                          />
                          <div>
                            <span className="font-medium text-primary">{role.label}</span>
                            <p className="text-sm text-gray-mid">{role.description}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Active Toggle (only for editing) */}
                  {isEditing && (
                    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-3">
                      <div>
                        <span className="font-medium text-primary">Usuário ativo</span>
                        <p className="text-sm text-gray-mid">
                          Usuários inativos não podem fazer login
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, active: !formData.active })}
                        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 ${
                          formData.active ? 'bg-accent' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
                            formData.active ? 'translate-x-5' : 'translate-x-0'
                          }`}
                        />
                      </button>
                    </div>
                  )}

                  {/* Error */}
                  {error && (
                    <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3 pt-4">
                    <button
                      type="button"
                      onClick={onClose}
                      className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-dark transition hover:bg-gray-light"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-50"
                    >
                      {loading ? 'Salvando...' : isEditing ? 'Salvar' : 'Adicionar'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
