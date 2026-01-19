'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import AdminSidebar from '@/components/admin/Sidebar';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, loading, isAuthenticated, hasRole } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (!hasRole('gestor')) {
        // Only gestores can access admin
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
  if (!isAuthenticated || !hasRole('gestor')) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-light">
      <AdminSidebar />

      {/* Main Content */}
      <main className="lg:pl-64">
        <div className="min-h-screen p-4 pt-16 lg:p-6 lg:pt-6">
          {children}
        </div>
      </main>
    </div>
  );
}
