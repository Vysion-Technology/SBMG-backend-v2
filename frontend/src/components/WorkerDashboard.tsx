import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, X } from 'lucide-react';
import { workerApi } from '../api';
import type { AssignedComplaintResponse } from '../types';

interface WorkerDashboardProps {
  user: any;
}

const WorkerDashboard: React.FC<WorkerDashboardProps> = ({ user }) => {
  const [complaints, setComplaints] = useState<AssignedComplaintResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedComplaint, setSelectedComplaint] = useState<AssignedComplaintResponse | null>(null);
  const [uploadingFile, setUploadingFile] = useState<number | null>(null);

  useEffect(() => {
    const loadComplaints = async () => {
      try {
        const data = await workerApi.getAssignedComplaints();
        setComplaints(data);
      } catch (error) {
        console.error('Error loading assigned complaints:', error);
      } finally {
        setLoading(false);
      }
    };
    loadComplaints();
  }, []);

  const handleFileUpload = async (complaintId: number, file: File) => {
    setUploadingFile(complaintId);
    try {
      await workerApi.uploadComplaintMedia(complaintId, file);
      // Refresh complaints to get updated media URLs
      const updatedComplaints = await workerApi.getAssignedComplaints();
      setComplaints(updatedComplaints);
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setUploadingFile(null);
    }
  };

  const markComplaintDone = async (complaintId: number) => {
    try {
      await workerApi.markComplaintDone(complaintId);
      // Refresh complaints
      const updatedComplaints = await workerApi.getAssignedComplaints();
      setComplaints(updatedComplaints);
    } catch (error) {
      console.error('Error marking complaint as done:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'assigned':
        return 'bg-yellow-100 text-yellow-800';
      case 'in_progress':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-lg text-gray-600">Loading your assigned tasks...</div>
      </div>
    );
  }

  return (
    <div className="px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Tasks</h1>
        <p className="text-gray-600 mt-1">
          Welcome {user.username}! Here are the complaints assigned to you.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="bg-yellow-500 p-3 rounded-md text-white">
                  <Upload size={24} />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Assigned</dt>
                  <dd className="text-2xl font-bold text-gray-900">{complaints.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="bg-orange-500 p-3 rounded-md text-white">
                  <Upload size={24} />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">In Progress</dt>
                  <dd className="text-2xl font-bold text-gray-900">
                    {complaints.filter(c => c.status_name === 'IN_PROGRESS').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="bg-green-500 p-3 rounded-md text-white">
                  <CheckCircle size={24} />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Completed</dt>
                  <dd className="text-2xl font-bold text-gray-900">
                    {complaints.filter(c => c.status_name === 'COMPLETED').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Complaints Grid */}
      <div className="grid gap-6">
        {complaints.map((complaint) => (
          <div key={complaint.id} className="bg-white shadow-sm rounded-lg border border-gray-200">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Complaint #{complaint.id}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {complaint.village_name}, {complaint.block_name}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(complaint.status_name)}`}>
                  {complaint.status_name.replace('_', ' ')}
                </span>
              </div>

              <div className="mb-4">
                <p className="text-gray-700">{complaint.description}</p>
              </div>

              {/* Contact Information */}
              {complaint.mobile_number && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-blue-800 mr-2">Contact:</span>
                    <span className="text-sm text-blue-700">{complaint.mobile_number}</span>
                  </div>
                </div>
              )}

              <div className="flex justify-between items-center text-sm text-gray-500 mb-4">
                <span>Created: {formatDate(complaint.created_at)}</span>
                {complaint.updated_at && (
                  <span>Updated: {formatDate(complaint.updated_at)}</span>
                )}
              </div>

              {/* Media Section */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium text-gray-700">Before/After Images</h4>
                  <div className="flex space-x-2">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          handleFileUpload(complaint.id, file);
                        }
                      }}
                      className="hidden"
                      id={`file-${complaint.id}`}
                    />
                    <label
                      htmlFor={`file-${complaint.id}`}
                      className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 cursor-pointer disabled:opacity-50"
                    >
                      {uploadingFile === complaint.id ? 'Uploading...' : 'Upload Image'}
                    </label>
                  </div>
                </div>

                {complaint.media_urls.length > 0 && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                    {complaint.media_urls.map((url, index) => (
                      <div key={index} className="bg-gray-100 rounded-md p-3 text-center text-sm text-gray-600">
                        Image {index + 1}
                        <br />
                        <span className="text-xs text-gray-500">
                          {url.split('/').pop()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex space-x-3 mt-4">
                  {complaint.status_name === 'ASSIGNED' && (
                    <button
                      onClick={() => markComplaintDone(complaint.id)}
                      className="bg-orange-500 text-white px-4 py-2 rounded-md hover:bg-orange-600 transition-colors"
                    >
                      Start Work
                    </button>
                  )}
                  
                  {complaint.status_name === 'IN_PROGRESS' && (
                    <button
                      onClick={() => markComplaintDone(complaint.id)}
                      className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 transition-colors"
                    >
                      Mark as Completed
                    </button>
                  )}

                  <button
                    onClick={() => setSelectedComplaint(complaint)}
                    className="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600 transition-colors"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}

        {complaints.length === 0 && (
          <div className="text-center py-12">
            <CheckCircle size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No complaints assigned to you yet</p>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedComplaint && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Complaint #{selectedComplaint.id} Details
                </h3>
                <button
                  onClick={() => setSelectedComplaint(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-700">Description</h4>
                  <p className="text-gray-600">{selectedComplaint.description}</p>
                </div>
                
                {selectedComplaint.mobile_number && (
                  <div>
                    <h4 className="font-medium text-gray-700">Contact Number</h4>
                    <p className="text-gray-600">{selectedComplaint.mobile_number}</p>
                  </div>
                )}
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-gray-700">Location</h4>
                    <p className="text-gray-600">
                      {selectedComplaint.village_name}, {selectedComplaint.block_name}, {selectedComplaint.district_name}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700">Status</h4>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedComplaint.status_name)}`}>
                      {selectedComplaint.status_name.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-gray-700">Created</h4>
                    <p className="text-gray-600">{formatDate(selectedComplaint.created_at)}</p>
                  </div>
                  {selectedComplaint.updated_at && (
                    <div>
                      <h4 className="font-medium text-gray-700">Last Updated</h4>
                      <p className="text-gray-600">{formatDate(selectedComplaint.updated_at)}</p>
                    </div>
                  )}
                </div>

                {selectedComplaint.media_urls.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Attached Images</h4>
                    <div className="grid grid-cols-3 gap-2">
                      {selectedComplaint.media_urls.map((_, index) => (
                        <div key={index} className="bg-gray-100 rounded-md p-3 text-center text-sm text-gray-600">
                          Image {index + 1}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkerDashboard;