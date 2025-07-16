import React, { ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import Sidebar from './Sidebar';
import Header from './Header';
import LoadingSpinner from '../UI/LoadingSpinner';

interface LayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title, subtitle }) => {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-secondary-900 mb-4">
            Authentication Required
          </h1>
          <p className="text-secondary-600">
            Please log in to access this page.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-secondary-50">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={title} subtitle={subtitle} />
        
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;