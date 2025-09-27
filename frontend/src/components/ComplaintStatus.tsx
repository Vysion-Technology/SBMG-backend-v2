import React, { useState } from 'react';
import { Search, AlertCircle, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { publicApi } from '../api';
import type { ComplaintStatusResponse } from '../types';

const ComplaintStatus: React.FC = () => {
  const [complaintId, setComplaintId] = useState('');
  const [complaint, setComplaint] = useState<ComplaintStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintId.trim()) {
      setError('Please enter a complaint ID');
      return;
    }

    setLoading(true);
    setError(null);
    setComplaint(null);

    try {
      const result = await publicApi.getComplaintStatus(Number(complaintId));
      setComplaint(result);
      
      // Save to recent searches in localStorage (for user dashboard)
      const userId = localStorage.getItem('current_user_id');
      if (userId) {
        const storageKey = `recent_searches_${userId}`;
        const existing = JSON.parse(localStorage.getItem(storageKey) || '[]');
        const updated = [Number(complaintId), ...existing.filter((id: number) => id !== Number(complaintId))].slice(0, 10);
        localStorage.setItem(storageKey, JSON.stringify(updated));
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

  const formatDate = (dateString: string) => {
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
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(complaint.status_name)}`}>
                    {complaint.status_name.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-medium text-gray-700 mb-1">Status</h3>
                    <p className="text-gray-600 capitalize">{complaint.status_name.replace('_', ' ')}</p>
                  </div>
                  {complaint.updated_at && (
                    <div>
                      <h3 className="font-medium text-gray-700 mb-1">Last Updated</h3>
                      <p className="text-gray-600">{formatDate(complaint.updated_at)}</p>
                    </div>
                  )}
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