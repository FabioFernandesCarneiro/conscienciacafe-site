'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import BottomNav from '@/components/BottomNav';
import AppSidebar from '@/components/AppSidebar';

export default function CaixaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { loading, isAuthenticated, hasRole } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (!hasRole('gerente') && !hasRole('gestor')) {
        // Only gerente and gestor can access caixa
        router.push('/');
      }
    }
  }, [loading, isAuthenticated, hasRole, router]);

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-light">
        <div className="text-gray-mid">Carregando...</div>
      </div>
    );
  }

  // Don't render if not authorized
  if (!isAuthenticated || (!hasRole('gerente') && !hasRole('gestor'))) {
    return null;
  }

  return (
    <>
      <AppSidebar />
      <div className="lg:pl-64">
        {children}
      </div>
      <BottomNav />
    </>
  );
}
