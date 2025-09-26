import React, { useState } from 'react';
import { MapPin, Settings, Users, FileText, Database } from 'lucide-react';
import GeographyManager from './GeographyManager';
import type { User } from '../types';

interface AdminPanelProps {
  user: User;
}

type AdminSection = 'dashboard' | 'geography' | 'users' | 'complaints' | 'settings';

const AdminPanel: React.FC<AdminPanelProps> = ({ user }) => {
  const [activeSection, setActiveSection] = useState<AdminSection>('dashboard');

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: FileText },
    { id: 'geography', label: 'Geography Management', icon: MapPin },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'complaints', label: 'Complaint Management', icon: Database },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'geography':
        return <GeographyManager />;
      case 'dashboard':
        return (
          <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Admin Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                <div className="flex items-center">
                  <MapPin className="w-8 h-8 text-blue-600" />
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold">Geography</h3>
                    <p className="text-gray-600">Manage districts, blocks, and villages</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-green-600" />
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold">Users</h3>
                    <p className="text-gray-600">Manage user accounts and roles</p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                <div className="flex items-center">
                  <Database className="w-8 h-8 text-purple-600" />
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold">Complaints</h3>
                    <p className="text-gray-600">Monitor and manage complaints</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return (
          <div className="p-6">
            <div className="text-center py-12">
              <h2 className="text-xl font-medium text-gray-900 mb-2">
                {menuItems.find(item => item.id === activeSection)?.label}
              </h2>
              <p className="text-gray-500">This section is coming soon.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-sm">
          <div className="p-6">
            <h2 className="text-xl font-bold text-gray-900">Admin Panel</h2>
            <p className="text-sm text-gray-600">Welcome, {user.username}</p>
          </div>
          <nav className="mt-6">
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id as AdminSection)}
                  className={`w-full flex items-center px-6 py-3 text-left hover:bg-gray-50 transition-colors ${
                    activeSection === item.id
                      ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-600'
                      : 'text-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;