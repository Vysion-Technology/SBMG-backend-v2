import React, { useState, useEffect } from 'react';
import { Search, AlertCircle, ExternalLink, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { publicApi } from '../api';
import type { ComplaintStatusResponse } from '../types';

const ComplaintStatus: React.FC = () => {
  const [complaintId, setComplaintId] = useState('');
  const [complaint, setComplaint] = useState<ComplaintStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useState<number[]>([]);
  const [searchParams] = useSearchParams();

  // Load recent searches from localStorage
  useEffect(() => {
    const userId = localStorage.getItem('current_user_id');
    if (userId) {
      const storageKey = `recent_searches_${userId}`;
      const existing = JSON.parse(localStorage.getItem(storageKey) || '[]');
      setRecentSearches(existing);
    }

    // If complaint ID is provided in URL, search automatically
    const urlComplaintId = searchParams.get('id');
    if (urlComplaintId) {
      setComplaintId(urlComplaintId);
      handleSearch(null, urlComplaintId);
    }
  }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = async (e?: React.FormEvent | null, id?: string) => {
    if (e) e.preventDefault();
    const searchId = id || complaintId;
    
    if (!searchId.trim()) {
      setError('Please enter a complaint ID');
      return;
    }

    setLoading(true);
    setError(null);
    setComplaint(null);

    try {
      const result = await publicApi.getComplaintStatus(Number(searchId));
      setComplaint(result);
      
      // Save to recent searches in localStorage (for user dashboard)
      const userId = localStorage.getItem('current_user_id');
      if (userId) {
        const storageKey = `recent_searches_${userId}`;
        const existing = JSON.parse(localStorage.getItem(storageKey) || '[]');
        const updated = [Number(searchId), ...existing.filter((id: number) => id !== Number(searchId))].slice(0, 10);
        localStorage.setItem(storageKey, JSON.stringify(updated));
        setRecentSearches(updated);
      }
    } catch (error: unknown) {
      console.error('Error fetching complaint:', error);
      let errorMessage = 'Failed to fetch complaint status. Please try again.';
      if (error instanceof Error && 'response' in error) {
        const axiosError = error as { response?: { status: number } };
        if (axiosError.response?.status === 404) {
          errorMessage = 'Complaint not found. Please check the ID and try again.';
        }
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
      case 'assigned':
        return <Clock className="w-5 h-5" />;
      case 'in_progress':
        return <AlertTriangle className="w-5 h-5" />;
      case 'completed':
      case 'verified':
      case 'closed':
        return <CheckCircle className="w-5 h-5" />;
      case 'invalid':
        return <XCircle className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'assigned':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'in_progress':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'verified':
        return 'text-emerald-600 bg-emerald-50 border-emerald-200';
      case 'closed':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'invalid':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const quickSearch = (id: number) => {
    setComplaintId(id.toString());
    handleSearch(null, id.toString());
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Track Complaint Status</h1>
          <p className="text-gray-600 mt-1">
            Enter your complaint ID to check the current status and progress.
          </p>
        </div>

        <div className="p-6">
          <form onSubmit={handleSearch} className="mb-6">
            <div className="flex">
              <div className="flex-1">
                <label htmlFor="complaint-id" className="sr-only">
                  Complaint ID
                </label>
                <input
                  type="text"
                  id="complaint-id"
                  value={complaintId}
                  onChange={(e) => setComplaintId(e.target.value)}
                  className="w-full border border-gray-300 rounded-l-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter complaint ID (e.g., 123)"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 text-white px-6 py-2 rounded-r-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                <Search size={20} />
                {loading && <span className="ml-2">Searching...</span>}
              </button>
            </div>
          </form>

          {/* Recent Searches */}
          {recentSearches.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Searches</h3>
              <div className="flex flex-wrap gap-2">
                {recentSearches.slice(0, 5).map(id => (
                  <button
                    key={id}
                    onClick={() => quickSearch(id)}
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    #{id}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
              <div className="flex">
                <AlertCircle className="text-red-400 mr-3 mt-0.5" size={20} />
                <p className="text-red-800">{error}</p>
              </div>
            </div>
          )}

          {complaint && (
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Complaint #{complaint.id}
                  </h2>
                  <div className={`flex items-center px-3 py-2 rounded-full border ${getStatusColor(complaint.status_name)}`}>
                    {getStatusIcon(complaint.status_name)}
                    <span className="ml-2 text-sm font-medium">
                      {complaint.status_name.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-medium text-gray-700 mb-1">Current Status</h3>
                    <p className="text-gray-600 capitalize">{complaint.status_name.replace('_', ' ')}</p>
                  </div>
                  {complaint.updated_at && (
                    <div>
                      <h3 className="font-medium text-gray-700 mb-1">Last Updated</h3>
                      <p className="text-gray-600">{formatDate(complaint.updated_at)}</p>
                    </div>
                  )}
                </div>
                
                {/* Status Progress */}
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">Progress</h3>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-300 ${
                          ['completed', 'verified', 'closed'].includes(complaint.status_name.toLowerCase()) 
                            ? 'bg-green-500 w-full' 
                            : complaint.status_name.toLowerCase() === 'in_progress' 
                            ? 'bg-orange-500 w-3/4' 
                            : complaint.status_name.toLowerCase() === 'assigned'
                            ? 'bg-yellow-500 w-1/2'
                            : 'bg-blue-500 w-1/4'
                        }`}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-500">
                      {complaint.status_name.toLowerCase() === 'closed' ? '100%' : 
                       complaint.status_name.toLowerCase() === 'completed' ? '90%' :
                       complaint.status_name.toLowerCase() === 'in_progress' ? '60%' :
                       complaint.status_name.toLowerCase() === 'assigned' ? '40%' : '20%'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">
                      Keep this complaint ID for future reference: <strong>#{complaint.id}</strong>
                    </p>
                  </div>
                  <div className="flex space-x-3">
                    <Link
                      to={`/complaint/${complaint.id}`}
                      className="inline-flex items-center text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                    >
                      <ExternalLink size={16} className="mr-1" />
                      View Details
                    </Link>
                    <button
                      onClick={() => {
                        setComplaint(null);
                        setComplaintId('');
                      }}
                      className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                    >
                      Search Another
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!complaint && !error && !loading && (
            <div className="text-center text-gray-500 py-8">
              <Search size={48} className="mx-auto text-gray-300 mb-4" />
              <p>Enter a complaint ID above to check its status</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ComplaintStatus;