import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

interface LayoutProps {
  children?: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {children || <Outlet />}
        </div>
      </main>
    </div>
  );
};

export default Layout;