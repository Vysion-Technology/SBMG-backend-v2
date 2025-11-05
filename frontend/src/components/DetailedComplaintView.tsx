import React, { useState, useEffect } from 'react';
import { FileText, User, Calendar, MapPin, Camera, MessageSquare, AlertCircle, CheckCircle, Clock, ArrowLeft } from 'lucide-react';
import { publicApi } from '../api';
import type { ComplaintDetailsResponse } from '../types';

interface DetailedComplaintViewProps {
  complaintId: number;
  onBack?: () => void;
}

const DetailedComplaintView: React.FC<DetailedComplaintViewProps> = ({ complaintId, onBack }) => {
  const [complaint, setComplaint] = useState<ComplaintDetailsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // API base URL for media files
  const API_BASE_URL = 'http://localhost:8000/api/v1';

  // Convert relative media URLs to full API URLs
  const getImageUrl = (mediaUrl: string) => {
    // If it's already a full URL (starts with http), return as-is
    if (mediaUrl.startsWith('http://') || mediaUrl.startsWith('https://')) {
      return mediaUrl;
    }
    
    // If it starts with /media/, it's a legacy local path format
    if (mediaUrl.startsWith('/media/')) {
      return `${API_BASE_URL}/public/media${mediaUrl}`;
    }
    
    // Otherwise, assume it's an S3 key and serve through our API
    return `${API_BASE_URL}/public/media/${mediaUrl}`;
  };

  const fetchComplaintDetails = React.useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await publicApi.getComplaintDetails(complaintId);
      setComplaint(result);
    } catch (error: unknown) {
      console.error('Error fetching complaint:', error);
      let errorMessage = 'Failed to fetch complaint details. Please try again.';
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
  }, [complaintId]);

  useEffect(() => {
    fetchComplaintDetails();
  }, [fetchComplaintDetails]);

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

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return <AlertCircle className="w-4 h-4" />;
      case 'assigned':
      case 'in_progress':
        return <Clock className="w-4 h-4" />;
      case 'completed':
      case 'verified':
      case 'resolved':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
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

  const isWorkerMedia = (url: string) => {
    return url.includes('/before') || url.includes('/after') || url.includes('/progress');
  };

  const getMediaType = (url: string) => {
    if (url.includes('/before')) return 'Before Work';
    if (url.includes('/after')) return 'After Work';
    if (url.includes('/progress')) return 'Work Progress';
    if (url.includes('/comments/')) return 'Comment Media';
    return 'Citizen Media';
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-8">
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white shadow-sm rounded-lg border border-gray-200">
          <div className="p-8">
            <div className="flex items-center mb-4">
              <AlertCircle className="w-6 h-6 text-red-500 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">Error Loading Complaint</h2>
            </div>
            <p className="text-gray-600 mb-4">{error}</p>
            {onBack && (
              <button
                onClick={onBack}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Go Back
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!complaint) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Complaint Details</h1>
              <p className="text-gray-600 mt-1">Complete information about complaint #{complaint.id}</p>
            </div>
            {onBack && (
              <button
                onClick={onBack}
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back
              </button>
            )}
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Status Card */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Current Status</h3>
                <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium border ${getStatusColor(complaint.status_name)}`}>
                  {getStatusIcon(complaint.status_name)}
                  <span className="ml-2">{complaint.status_name.replace('_', ' ').toUpperCase()}</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Complaint ID</p>
                <p className="text-2xl font-bold text-gray-900">#{complaint.id}</p>
              </div>
            </div>
          </div>

          {/* Basic Information */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2 text-indigo-600" />
                Complaint Information
              </h4>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-500 block">Type:</span>
                  <span className="font-medium text-gray-900">{complaint.complaint_type_name}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500 block">Description:</span>
                  <p className="mt-1 text-gray-900 leading-relaxed">{complaint.description}</p>
                </div>
                {complaint.mobile_number && (
                  <div>
                    <span className="text-sm text-gray-500 block">Mobile Number:</span>
                    <span className="font-medium text-gray-900">{complaint.mobile_number}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <MapPin className="w-5 h-5 mr-2 text-red-600" />
                Location Details
              </h4>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-500 block">District:</span>
                  <span className="font-medium text-gray-900">{complaint.district_name}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500 block">Block:</span>
                  <span className="font-medium text-gray-900">{complaint.block_name}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500 block">Village:</span>
                  <span className="font-medium text-gray-900">{complaint.village_name}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Timeline and Assignment */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-blue-600" />
                Timeline
              </h4>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-gray-500 block">Created:</span>
                  <span className="font-medium text-gray-900">{formatDate(complaint.created_at)}</span>
                </div>
                {complaint.updated_at && (
                  <div>
                    <span className="text-sm text-gray-500 block">Last Updated:</span>
                    <span className="font-medium text-gray-900">{formatDate(complaint.updated_at)}</span>
                  </div>
                )}
              </div>
            </div>

            {complaint.assigned_worker && (
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <User className="w-5 h-5 mr-2 text-green-600" />
                  Assignment
                </h4>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-gray-500 block">Assigned Worker:</span>
                    <span className="font-medium text-gray-900">{complaint.assigned_worker}</span>
                  </div>
                  {complaint.assignment_date && (
                    <div>
                      <span className="text-sm text-gray-500 block">Assigned On:</span>
                      <span className="font-medium text-gray-900">{formatDate(complaint.assignment_date)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Media Section */}
          {complaint.media_urls && complaint.media_urls.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Camera className="w-5 h-5 mr-2 text-purple-600" />
                Media & Photos ({complaint.media_urls.length})
              </h4>
              
              {/* Categorize media */}
              <div className="space-y-6">
                {/* Citizen Media */}
                {complaint.media_urls.filter(url => !isWorkerMedia(url) && !url.includes('/comments/')).length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-700 mb-3">Citizen's Complaint Photos</h5>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {complaint.media_urls
                        .filter(url => !isWorkerMedia(url) && !url.includes('/comments/'))
                        .map((url, index) => (
                          <div key={index} className="relative group">
                            <img 
                              src={getImageUrl(url)} 
                              alt={`Citizen media ${index + 1}`}
                              className="w-full h-32 object-cover rounded-lg border border-gray-200 group-hover:shadow-lg transition-shadow cursor-pointer"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = '/placeholder-image.png';
                              }}
                              onClick={() => window.open(getImageUrl(url), '_blank')}
                            />
                            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-lg transition-all cursor-pointer"></div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Worker Media */}
                {complaint.media_urls.filter(url => isWorkerMedia(url)).length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-700 mb-3">Worker's Documentation</h5>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {complaint.media_urls
                        .filter(url => isWorkerMedia(url))
                        .map((url, index) => (
                          <div key={index} className="relative group">
                            <div className="relative">
                              <img 
                                src={getImageUrl(url)} 
                                alt={`Worker media ${index + 1}`}
                                className="w-full h-32 object-cover rounded-lg border border-gray-200 group-hover:shadow-lg transition-shadow cursor-pointer"
                                onError={(e) => {
                                  const target = e.target as HTMLImageElement;
                                  target.src = '/placeholder-image.png';
                                }}
                                onClick={() => window.open(getImageUrl(url), '_blank')}
                              />
                              <div className="absolute top-2 left-2">
                                <span className="bg-white bg-opacity-90 text-xs font-medium px-2 py-1 rounded">
                                  {getMediaType(url)}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Comment Media */}
                {complaint.media_urls.filter(url => url.includes('/comments/')).length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-700 mb-3">Comment Attachments</h5>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {complaint.media_urls
                        .filter(url => url.includes('/comments/'))
                        .map((url, index) => (
                          <div key={index} className="relative group">
                            <img 
                              src={getImageUrl(url)} 
                              alt={`Comment media ${index + 1}`}
                              className="w-full h-32 object-cover rounded-lg border border-gray-200 group-hover:shadow-lg transition-shadow cursor-pointer"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = '/placeholder-image.png';
                              }}
                              onClick={() => window.open(getImageUrl(url), '_blank')}
                            />
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Comments & Updates */}
          {complaint.comments && complaint.comments.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <MessageSquare className="w-5 h-5 mr-2 text-orange-600" />
                Comments & Updates ({complaint.comments.length})
              </h4>
              <div className="space-y-4">
                {complaint.comments
                  .sort((a, b) => new Date(a.commented_at).getTime() - new Date(b.commented_at).getTime())
                  .map((comment) => (
                    <div key={comment.id} className="flex space-x-4 p-4 bg-gray-50 rounded-lg">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-indigo-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h5 className="text-sm font-medium text-gray-900">{comment.user_name}</h5>
                          <span className="text-xs text-gray-500">{formatDate(comment.commented_at)}</span>
                        </div>
                        <p className="text-gray-700 leading-relaxed">{comment.comment}</p>
                        
                        {/* Check if comment is a resolution or verification */}
                        {(comment.comment.includes('[RESOLVED]') || comment.comment.includes('VERIFIED') || comment.comment.includes('citizen via mobile')) && (
                          <div className="mt-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Status Update
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DetailedComplaintView;