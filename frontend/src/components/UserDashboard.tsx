import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Bell, 
  User, 
  Activity,
  CheckCircle
} from 'lucide-react';
import { publicApi } from '../api';
import type { User as UserType, ComplaintStatusResponse, ComplaintDetailsResponse } from '../types';

interface UserDashboardProps {
  user: UserType;
}

const UserDashboard: React.FC<UserDashboardProps> = ({ user }) => {
  const [recentSearches, setRecentSearches] = useState<number[]>([]);
  const [complaintStatuses, setComplaintStatuses] = useState<{ [key: number]: ComplaintStatusResponse }>({});
  const [publicComplaints, setPublicComplaints] = useState<ComplaintDetailsResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);

  // Load recent complaint searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(`recent_searches_${user.id}`);
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, [user.id]);

  // Load status for recent searches
  useEffect(() => {
    const loadComplaintStatuses = async () => {
      if (recentSearches.length === 0) return;
      
      setLoading(true);
      const statuses: { [key: number]: ComplaintStatusResponse } = {};
      
      for (const complaintId of recentSearches.slice(0, 5)) { // Only show last 5
        try {
          const status = await publicApi.getComplaintStatus(complaintId);
          statuses[complaintId] = status;
        } catch (error) {
          console.error(`Failed to load status for complaint ${complaintId}:`, error);
        }
      }
      
      setComplaintStatuses(statuses);
      setLoading(false);
    };

    loadComplaintStatuses();
  }, [recentSearches]);

  // Load public complaint data for insights
  useEffect(() => {
    const loadPublicData = async () => {
      setStatsLoading(true);
      try {
        // Get recent public complaints (last 20)
        const complaints = await publicApi.getPublicComplaints(undefined, undefined, undefined, 0, 20);
        setPublicComplaints(complaints);
      } catch (error) {
        console.error('Failed to load public complaint data:', error);
      } finally {
        setStatsLoading(false);
      }
    };

    loadPublicData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'bg-blue-100 text-blue-800';
      case 'assigned':
        return 'bg-yellow-100 text-yellow-800';
      case 'in_progress':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'verified':
        return 'bg-emerald-100 text-emerald-800';
      case 'closed':
        return 'bg-gray-100 text-gray-800';
      case 'invalid':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not updated';
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome, {user.username}!
          </h1>
          <p className="text-gray-600">
            Your personal dashboard to track complaints and access services
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow cursor-pointer"
               onClick={() => window.location.href = '/create-complaint'}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Create New Complaint
                </h3>
                <p className="text-gray-600 text-sm">
                  Submit a new complaint about sanitation issues
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow cursor-pointer"
               onClick={() => window.location.href = '/complaint-status'}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Track Complaint
                </h3>
                <p className="text-gray-600 text-sm">
                  Check the status of your complaints
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <Search className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow cursor-pointer">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Your Profile
                </h3>
                <p className="text-gray-600 text-sm">
                  View and update your profile information
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <User className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* User Info Card */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <User className="w-5 h-5 mr-2" />
            Your Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Username</p>
              <p className="font-semibold text-gray-900">{user.username}</p>
            </div>
            {user.email && (
              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-semibold text-gray-900">{user.email}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-600">Account Status</p>
              <p className={`font-semibold ${user.is_active ? 'text-green-600' : 'text-red-600'}`}>
                {user.is_active ? 'Active' : 'Inactive'}
              </p>
            </div>
            {user.roles && user.roles.length > 0 && (
              <div>
                <p className="text-sm text-gray-600">Roles</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {user.roles.map((role, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                      {role}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Public Complaint Insights */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            Recent Community Complaints
          </h2>
          {statsLoading ? (
            <div className="text-center py-4">
              <Activity className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
              <p className="text-gray-600">Loading complaint data...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">Total Complaints</h3>
                <p className="text-2xl font-bold text-blue-700">{publicComplaints.length}</p>
                <p className="text-sm text-blue-600">Recent complaints</p>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="font-semibold text-green-900 mb-2">Status Distribution</h3>
                <div className="space-y-1">
                  {Object.entries(
                    publicComplaints.reduce((acc, complaint) => {
                      acc[complaint.status_name] = (acc[complaint.status_name] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).slice(0, 3).map(([status, count]) => (
                    <div key={status} className="flex justify-between text-sm">
                      <span className="text-green-700">{status.replace('_', ' ')}</span>
                      <span className="font-medium text-green-800">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-purple-50 rounded-lg p-4">
                <h3 className="font-semibold text-purple-900 mb-2">Recent Activity</h3>
                <p className="text-2xl font-bold text-purple-700">
                  {publicComplaints.filter(c => {
                    const createdDate = new Date(c.created_at);
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    return createdDate > weekAgo;
                  }).length}
                </p>
                <p className="text-sm text-purple-600">This week</p>
              </div>
            </div>
          )}
          
          {publicComplaints.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold text-gray-900 mb-3">Recent Complaints in Your Area</h3>
              <div className="space-y-2">
                {publicComplaints.slice(0, 5).map((complaint) => (
                  <div key={complaint.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">#{complaint.id}</p>
                      <p className="text-sm text-gray-600">{complaint.village_name}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(complaint.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(complaint.status_name)}`}>
                      {complaint.status_name.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Recent Complaint Searches */}
        {recentSearches.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Recently Tracked Complaints
            </h2>
            {loading ? (
              <div className="text-center py-4">
                <Activity className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-600" />
                <p className="text-gray-600">Loading complaint statuses...</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentSearches.slice(0, 5).map((complaintId) => {
                  const status = complaintStatuses[complaintId];
                  return (
                    <div key={complaintId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="mr-4">
                          <p className="font-semibold text-gray-900">Complaint #{complaintId}</p>
                          {status && (
                            <p className="text-sm text-gray-600">
                              Last updated: {formatDate(status.updated_at)}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        {status ? (
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status.status_name)}`}>
                            {status.status_name.replace('_', ' ')}
                          </span>
                        ) : (
                          <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                            Not found
                          </span>
                        )}
                        <button
                          onClick={() => window.location.href = '/complaint-status'}
                          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Quick Tips */}
        <div className="mt-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Bell className="w-5 h-5 mr-2" />
            Quick Tips
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start">
              <CheckCircle className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium">Track Your Complaints</p>
                <p className="text-blue-100 text-sm">Save your complaint ID to track status updates</p>
              </div>
            </div>
            <div className="flex items-start">
              <CheckCircle className="w-5 h-5 mr-2 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium">Provide Clear Details</p>
                <p className="text-blue-100 text-sm">Include specific location and issue description</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;