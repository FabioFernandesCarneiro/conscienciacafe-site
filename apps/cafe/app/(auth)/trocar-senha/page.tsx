'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LockClosedIcon, ExclamationTriangleIcon, CheckCircleIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/lib/hooks/useAuth';
import { changePassword } from '@/lib/firebase/auth';

export default function TrocarSenhaPage() {
  const router = useRouter();
  const { isAuthenticated, loading, isEmailPasswordUser } = useAuth();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Redirect if not authenticated or not email/password user
  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (!isEmailPasswordUser) {
        // Google users can't change password here
        router.push('/');
      }
    }
  }, [isAuthenticated, loading, isEmailPasswordUser, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!currentPassword) {
      setError('Digite sua senha atual');
      return;
    }

    if (!newPassword) {
      setError('Digite a nova senha');
      return;
    }

    if (newPassword.length < 6) {
      setError('A nova senha deve ter pelo menos 6 caracteres');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('As senhas não conferem');
      return;
    }

    if (currentPassword === newPassword) {
      setError('A nova senha deve ser diferente da atual');
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await changePassword(currentPassword, newPassword);

      if (result.success) {
        setSuccess(true);
        // Clear form
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        // Redirect after a moment
        setTimeout(() => {
          router.push('/');
        }, 2000);
      } else {
        setError(result.error || 'Erro ao trocar senha');
      }
    } catch (err) {
      setError('Erro inesperado ao trocar senha');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-gray-mid">Carregando...</div>
      </div>
    );
  }

  // Don't render if not authorized
  if (!isAuthenticated || !isEmailPasswordUser) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        {/* Back Button */}
        <button
          onClick={() => router.back()}
          className="mb-4 flex items-center gap-2 text-sm text-gray-mid hover:text-primary transition"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Voltar
        </button>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-primary">
            Trocar Senha
          </h1>
          <p className="mt-2 text-gray-mid">
            Digite sua senha atual e escolha uma nova senha
          </p>
        </div>

        {/* Success Message */}
        {success && (
          <div className="mb-4 flex items-start gap-2 rounded-lg bg-green-50 p-3 text-green-700">
            <CheckCircleIcon className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <span className="text-sm">Senha alterada com sucesso! Redirecionando...</span>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-lg bg-red-50 p-3 text-red-700">
            <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Form */}
        <div className="rounded-2xl bg-white p-6 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Current Password */}
            <div>
              <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-dark">
                Senha Atual
              </label>
              <div className="relative mt-1">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <LockClosedIcon className="h-5 w-5 text-gray-mid" />
                </div>
                <input
                  id="currentPassword"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Sua senha atual"
                  disabled={isSubmitting || success}
                  className="block w-full rounded-lg border border-gray-300 py-3 pl-10 pr-3 text-primary placeholder:text-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:bg-gray-light disabled:cursor-not-allowed"
                />
              </div>
            </div>

            {/* New Password */}
            <div>
              <label htmlFor="newPassword" className="block text-sm font-medium text-gray-dark">
                Nova Senha
              </label>
              <div className="relative mt-1">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <LockClosedIcon className="h-5 w-5 text-gray-mid" />
                </div>
                <input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Nova senha (mínimo 6 caracteres)"
                  disabled={isSubmitting || success}
                  className="block w-full rounded-lg border border-gray-300 py-3 pl-10 pr-3 text-primary placeholder:text-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:bg-gray-light disabled:cursor-not-allowed"
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-dark">
                Confirmar Nova Senha
              </label>
              <div className="relative mt-1">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <LockClosedIcon className="h-5 w-5 text-gray-mid" />
                </div>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirme a nova senha"
                  disabled={isSubmitting || success}
                  className="block w-full rounded-lg border border-gray-300 py-3 pl-10 pr-3 text-primary placeholder:text-gray-mid focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:bg-gray-light disabled:cursor-not-allowed"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || success}
              className="w-full rounded-lg bg-accent py-3 font-medium text-white transition hover:bg-accent-hover focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Alterando...' : 'Alterar Senha'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
