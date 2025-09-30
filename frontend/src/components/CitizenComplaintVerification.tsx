import React, { useState } from 'react';
import { Search, AlertCircle, FileText, User, Calendar, MapPin, Camera } from 'lucide-react';
import { publicApi } from '../api';
import type { 
  ComplaintDetailsResponse
} from '../types';

const CitizenComplaintVerification: React.FC = () => {
  const [complaintId, setComplaintId] = useState('');
  const [complaint, setComplaint] = useState<ComplaintDetailsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetchComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintId.trim()) {
      setError('Please enter a complaint ID');
      return;
    }

    setLoading(true);
    setError(null);
    setComplaint(null);

    try {
      const result = await publicApi.getComplaintDetails(Number(complaintId));
      setComplaint(result);
    } catch (error: any) {
      console.error('Error fetching complaint:', error);
      if (error.response?.status === 404) {
        setError('Complaint not found. Please check the ID and try again.');
      } else {
        setError('Failed to fetch complaint details. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'assigned':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'in_progress':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'verified':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'resolved':
        return 'bg-teal-100 text-teal-800 border-teal-200';
      case 'closed':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'invalid':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
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
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Verify Complaint Resolution</h1>
          <p className="text-gray-600 mt-1">
            Check your complaint details and verify resolution status using your complaint ID and mobile number.
          </p>
        </div>

        <div className="p-6">
          {/* Search Form */}
          <form onSubmit={handleFetchComplaint} className="mb-6">
            <div className="mb-4">
              <label htmlFor="complaint-id" className="block text-sm font-medium text-gray-700 mb-1">
                Complaint ID *
              </label>
              <input
                type="text"
                id="complaint-id"
                value={complaintId}
                onChange={(e) => setComplaintId(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter complaint ID (e.g., 123)"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Search className="w-4 h-4 mr-2" />
              {loading ? 'Loading...' : 'Get Complaint Details'}
            </button>
          </form>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <div className="ml-3">
                  <p className="text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Complaint Details */}
          {complaint && (
            <div className="space-y-6">
              {/* Status */}
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Current Status</h3>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(complaint.status_name)}`}>
                      {complaint.status_name.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Basic Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                    <FileText className="w-4 h-4 mr-2" />
                    Complaint Details
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm text-gray-500">ID:</span>
                      <span className="ml-2 font-medium">#{complaint.id}</span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Type:</span>
                      <span className="ml-2">{complaint.complaint_type_name}</span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Description:</span>
                      <p className="mt-1 text-gray-900">{complaint.description}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    Location Details
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm text-gray-500">District:</span>
                      <span className="ml-2">{complaint.district_name}</span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Block:</span>
                      <span className="ml-2">{complaint.block_name}</span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-500">Village:</span>
                      <span className="ml-2">{complaint.village_name}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                  <Calendar className="w-4 h-4 mr-2" />
                  Timeline
                </h4>
                <div className="space-y-2">
                  <div>
                    <span className="text-sm text-gray-500">Created:</span>
                    <span className="ml-2">{formatDate(complaint.created_at)}</span>
                  </div>
                  {complaint.updated_at && (
                    <div>
                      <span className="text-sm text-gray-500">Last Updated:</span>
                      <span className="ml-2">{formatDate(complaint.updated_at)}</span>
                    </div>
                  )}
                  {complaint.assigned_worker && (
                    <div>
                      <span className="text-sm text-gray-500">Assigned Worker:</span>
                      <span className="ml-2 flex items-center">
                        <User className="w-4 h-4 mr-1" />
                        {complaint.assigned_worker}
                      </span>
                      {complaint.assignment_date && (
                        <span className="ml-2 text-sm text-gray-500">
                          on {formatDate(complaint.assignment_date)}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Media */}
              {complaint.media_urls && complaint.media_urls.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                    <Camera className="w-4 h-4 mr-2" />
                    Media ({complaint.media_urls.length})
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {complaint.media_urls.map((url, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-2">
                        <img 
                          src={url} 
                          alt={`Complaint media ${index + 1}`}
                          className="w-full h-24 object-cover rounded"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src = '/placeholder-image.png';
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Comments */}
              {complaint.comments && complaint.comments.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Comments & Updates ({complaint.comments.length})</h4>
                  <div className="space-y-4">
                    {complaint.comments.map((comment) => (
                      <div key={comment.id} className="border-l-4 border-gray-200 pl-4">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-900">{comment.user_name}</span>
                          <span className="text-sm text-gray-500">{formatDate(comment.commented_at)}</span>
                        </div>
                        <p className="text-gray-700">{comment.comment}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CitizenComplaintVerification;