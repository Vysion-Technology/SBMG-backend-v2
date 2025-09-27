import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Users, 
  TrendingUp, 
  MapPin, 
  Activity, 
  BarChart3 
} from 'lucide-react';
import { staffApi } from '../api';
import type { ComplaintResponse, DashboardStats, User } from '../types';
import { getUserHighestRole, getUserFullName } from '../utils';

interface DashboardProps {
  user: User;
}

const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const [complaints, setComplaints] = useState<ComplaintResponse[]>([]);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        // Use new consolidated reporting endpoints
        const complaintsData = await staffApi.getComplaints();
        setComplaints(complaintsData);
        
        const statsData = await staffApi.getDashboardStats();
        setDashboardStats(statsData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-subtle flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="container-custom py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="heading-primary">
            {getUserHighestRole(user) === 'ADMIN' ? 'Admin Dashboard' : 'Staff Dashboard'}
          </h1>
          <p className="text-gray-600 mt-2">
            Welcome back, {getUserFullName(user)}! Here's your overview.
          </p>
        </div>

        {/* Admin Statistics */}
        {getUserHighestRole(user) === 'ADMIN' && dashboardStats && (
          <div className="mb-8">
            <h2 className="heading-secondary mb-6">System Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card-modern">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Complaints</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardStats.total_complaints}
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-primary rounded-full">
                    <FileText className="w-6 h-6 text-white" />
                  </div>
                </div>
              </div>

              <div className="card-modern">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Users</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardStats?.total_users || 0}
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-success rounded-full">
                    <Users className="w-6 h-6 text-white" />
                  </div>
                </div>
              </div>

              <div className="card-modern">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Districts</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardStats?.total_districts || 0}
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-warning rounded-full">
                    <MapPin className="w-6 h-6 text-white" />
                  </div>
                </div>
              </div>

              <div className="card-modern">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Blocks</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboardStats?.total_blocks || 0}
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-info rounded-full">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                </div>
              </div>
            </div>

            {/* Status Distribution */}
            <div className="mt-8 card-modern">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
                Complaint Status Overview
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {dashboardStats && Object.entries(dashboardStats.complaints_by_status).map(([status, count]) => (
                  <div key={status} className="text-center">
                    <p className="text-2xl font-bold text-gray-900">{count}</p>
                    <p className="text-sm text-gray-600 capitalize">{status.replace('_', ' ')}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Districts Overview */}
            <div className="mt-6 card-modern">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <MapPin className="w-5 h-5 mr-2 text-green-600" />
                Top Districts by Complaints
              </h3>
              <div className="space-y-2">
                {dashboardStats?.complaints_by_district?.slice(0, 5).map((item) => (
                  <div key={item.district} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{item.district}</span>
                    <span className="badge badge-secondary">{item.count}</span>
                  </div>
                )) || (
                  <p className="text-sm text-gray-500">No district data available</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Recent Complaints */}
        <div className="card-modern">
          <div className="flex items-center justify-between mb-6">
            <h2 className="heading-secondary">Recent Complaints</h2>
            <span className="text-sm text-gray-500">
              {complaints.length} total complaints
            </span>
          </div>

          <div className="space-y-4">
            {complaints.slice(0, 10).map((complaint) => (
              <div key={complaint.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">#{complaint.id} - Complaint</h3>
                    <p className="text-sm text-gray-600 mt-1">{complaint.description}</p>
                    <div className="flex items-center mt-2 text-sm text-gray-500">
                      <MapPin className="w-4 h-4 mr-1" />
                      {complaint.village_name}, {complaint.block_name}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      complaint.status_name === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                      complaint.status_name === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
                      complaint.status_name === 'RESOLVED' ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {complaint.status_name}
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(complaint.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
