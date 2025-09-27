import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, X, FileText, AlertCircle } from 'lucide-react';
import { workerApi } from '../api';
import type { WorkerTaskResponse, User } from '../types';

interface WorkerDashboardProps {
  user: User;
}

const WorkerDashboard: React.FC<WorkerDashboardProps> = ({ user }) => {
  const [tasks, setTasks] = useState<WorkerTaskResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<WorkerTaskResponse | null>(null);
  const [uploadingFile, setUploadingFile] = useState<number | null>(null);
  const [resolvingComplaint, setResolvingComplaint] = useState<number | null>(null);
  const [resolutionComment, setResolutionComment] = useState('');
  const [resolutionFile, setResolutionFile] = useState<File | null>(null);

  // Get user role information for RBAC
  const userRole = user.roles?.[0] || '';
  const isWorker = userRole === 'WORKER';
  const isVDO = userRole === 'VDO';
  
  useEffect(() => {
    const loadTasks = async () => {
      try {
        // Use new consolidated endpoint
        const data = await workerApi.getAssignedTasks();
        setTasks(data);
      } catch (error) {
        console.error('Error loading assigned tasks:', error);
        // Fallback to legacy endpoint if new one fails
        try {
          const legacyData = await workerApi.getAssignedComplaints();
          // Convert legacy format to new format
          const convertedTasks: WorkerTaskResponse[] = legacyData.map(complaint => ({
            id: complaint.id,
            description: complaint.description,
            status_name: complaint.status_name,
            village_name: complaint.village_name,
            block_name: complaint.block_name,
            district_name: complaint.district_name,
            assigned_date: null,
            due_date: null,
            priority: 'NORMAL',
            media_urls: complaint.media_urls,
            completion_percentage: complaint.status_name === 'COMPLETED' ? 100 : 
                                   complaint.status_name === 'IN_PROGRESS' ? 50 : 0
          }));
          setTasks(convertedTasks);
        } catch (legacyError) {
          console.error('Error loading legacy assigned complaints:', legacyError);
        }
      } finally {
        setLoading(false);
      }
    };
    loadTasks();
  }, []);

  const canUploadMedia = (task: WorkerTaskResponse): boolean => {
    // Workers can upload media for tasks in progress or completed
    return (isWorker || isVDO) && ['IN_PROGRESS', 'ASSIGNED'].includes(task.status_name);
  };

  const canMarkCompleted = (task: WorkerTaskResponse): boolean => {
    // Workers can mark tasks as completed if they're in progress or assigned
    return isWorker && ['IN_PROGRESS', 'ASSIGNED'].includes(task.status_name);
  };

  const canResolveComplaint = (task: WorkerTaskResponse): boolean => {
    // VDOs can resolve completed complaints
    return isVDO && task.status_name === 'COMPLETED';
  };

  const handleFileUpload = async (taskId: number, file: File) => {
    if (!canUploadMedia(tasks.find(t => t.id === taskId)!)) {
      alert('You cannot upload media for this task in its current status.');
      return;
    }

    setUploadingFile(taskId);
    try {
      await workerApi.uploadComplaintMedia(taskId, file);
      // Refresh tasks to get updated media URLs
      const updatedTasks = await workerApi.getAssignedTasks();
      setTasks(updatedTasks);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload image. Please try again.');
    } finally {
      setUploadingFile(null);
    }
  };

  const markComplaintCompleted = async (taskId: number) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task || !canMarkCompleted(task)) {
      alert('You cannot mark this task as completed.');
      return;
    }

    try {
      await workerApi.markComplaintCompleted(taskId);
      // Refresh tasks
      const updatedTasks = await workerApi.getAssignedTasks();
      setTasks(updatedTasks);
    } catch (error) {
      console.error('Error marking complaint as completed:', error);
      alert('Failed to mark complaint as completed. Please try again.');
    }
  };

  const handleResolveComplaint = async (taskId: number) => {
    const task = tasks.find(t => t.id === taskId);
    if (!task || !canResolveComplaint(task)) {
      alert('You cannot resolve this complaint.');
      return;
    }

    if (!resolutionComment.trim()) {
      alert('Please provide a resolution comment.');
      return;
    }

    setResolvingComplaint(taskId);
    try {
      await workerApi.resolveComplaint(taskId, resolutionComment, resolutionFile || undefined);
      // Refresh tasks
      const updatedTasks = await workerApi.getAssignedTasks();
      setTasks(updatedTasks);
      setResolvingComplaint(null);
      setResolutionComment('');
      setResolutionFile(null);
    } catch (error) {
      console.error('Error resolving complaint:', error);
      alert('Failed to resolve complaint. Please try again.');
    } finally {
      setResolvingComplaint(null);
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
      case 'verified':
        return 'bg-blue-100 text-blue-800';
      case 'closed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
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
          Welcome {user.username} ({userRole})! Here are the complaints assigned to you.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="bg-blue-500 p-3 rounded-md text-white">
                  <FileText size={24} />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Assigned</dt>
                  <dd className="text-2xl font-bold text-gray-900">{tasks.length}</dd>
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
                    {tasks.filter(c => c.status_name === 'IN_PROGRESS').length}
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
                    {tasks.filter(c => c.status_name === 'COMPLETED').length}
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
                <div className="bg-red-500 p-3 rounded-md text-white">
                  <AlertCircle size={24} />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">High Priority</dt>
                  <dd className="text-2xl font-bold text-gray-900">
                    {tasks.filter(c => c.priority === 'HIGH').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tasks Grid */}
      <div className="grid gap-6">
        {tasks.map((task) => (
          <div key={task.id} className="bg-white shadow-sm rounded-lg border border-gray-200">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Complaint #{task.id}
                    </h3>
                    {task.priority !== 'NORMAL' && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(task.priority)}`}>
                        {task.priority} Priority
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">
                    {task.village_name}, {task.block_name}, {task.district_name}
                  </p>
                </div>
                <div className="flex flex-col items-end space-y-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(task.status_name)}`}>
                    {task.status_name.replace('_', ' ')}
                  </span>
                  {task.completion_percentage > 0 && (
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                          style={{width: `${task.completion_percentage}%`}}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-500">{task.completion_percentage}%</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mb-4">
                <p className="text-gray-700">{task.description}</p>
              </div>

              {/* Task Timeline */}
              <div className="mb-4 text-sm text-gray-500 space-y-1">
                {task.assigned_date && (
                  <div>Assigned: {formatDate(task.assigned_date)}</div>
                )}
                {task.due_date && (
                  <div className="text-orange-600">Due: {formatDate(task.due_date)}</div>
                )}
              </div>

              {/* Media Section */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium text-gray-700">Progress Images ({task.media_urls.length})</h4>
                  {canUploadMedia(task) && (
                    <div className="flex space-x-2">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            handleFileUpload(task.id, file);
                          }
                        }}
                        className="hidden"
                        id={`file-${task.id}`}
                      />
                      <label
                        htmlFor={`file-${task.id}`}
                        className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 cursor-pointer disabled:opacity-50"
                      >
                        {uploadingFile === task.id ? 'Uploading...' : 'Upload Image'}
                      </label>
                    </div>
                  )}
                </div>

                {task.media_urls.length > 0 && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                    {task.media_urls.map((url, index) => (
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

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3 mt-4">
                  {canMarkCompleted(task) && (
                    <>
                      {task.status_name === 'ASSIGNED' && (
                        <button
                          onClick={() => markComplaintCompleted(task.id)}
                          className="bg-orange-500 text-white px-4 py-2 rounded-md hover:bg-orange-600 transition-colors"
                        >
                          Start Work
                        </button>
                      )}
                      
                      {task.status_name === 'IN_PROGRESS' && (
                        <button
                          onClick={() => markComplaintCompleted(task.id)}
                          className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 transition-colors"
                        >
                          Mark as Completed
                        </button>
                      )}
                    </>
                  )}

                  {canResolveComplaint(task) && (
                    <button
                      onClick={() => setResolvingComplaint(task.id)}
                      className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition-colors"
                    >
                      Resolve & Close
                    </button>
                  )}

                  <button
                    onClick={() => setSelectedTask(task)}
                    className="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600 transition-colors"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}

        {tasks.length === 0 && (
          <div className="text-center py-12">
            <CheckCircle size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">No tasks assigned to you yet</p>
          </div>
        )}
      </div>

      {/* Resolution Modal */}
      {resolvingComplaint && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Resolve Complaint #{resolvingComplaint}
                </h3>
                <button
                  onClick={() => {
                    setResolvingComplaint(null);
                    setResolutionComment('');
                    setResolutionFile(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Resolution Comment *
                  </label>
                  <textarea
                    value={resolutionComment}
                    onChange={(e) => setResolutionComment(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Describe how the complaint was resolved..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Resolution Image (Optional)
                  </label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setResolutionFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => handleResolveComplaint(resolvingComplaint)}
                    disabled={!resolutionComment.trim() || resolvingComplaint === null}
                    className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Resolve & Close Complaint
                  </button>
                  <button
                    onClick={() => {
                      setResolvingComplaint(null);
                      setResolutionComment('');
                      setResolutionFile(null);
                    }}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Task #{selectedTask.id} Details
                </h3>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X size={20} />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-700">Description</h4>
                  <p className="text-gray-600">{selectedTask.description}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-gray-700">Location</h4>
                    <p className="text-gray-600">
                      {selectedTask.village_name}, {selectedTask.block_name}, {selectedTask.district_name}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700">Status</h4>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedTask.status_name)}`}>
                      {selectedTask.status_name.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-gray-700">Priority</h4>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${getPriorityColor(selectedTask.priority)}`}>
                      {selectedTask.priority}
                    </span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-700">Progress</h4>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{width: `${selectedTask.completion_percentage}%`}}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-500">{selectedTask.completion_percentage}%</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {selectedTask.assigned_date && (
                    <div>
                      <h4 className="font-medium text-gray-700">Assigned Date</h4>
                      <p className="text-gray-600">{formatDate(selectedTask.assigned_date)}</p>
                    </div>
                  )}
                  {selectedTask.due_date && (
                    <div>
                      <h4 className="font-medium text-gray-700">Due Date</h4>
                      <p className="text-gray-600">{formatDate(selectedTask.due_date)}</p>
                    </div>
                  )}
                </div>

                {selectedTask.media_urls.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Attached Images</h4>
                    <div className="grid grid-cols-3 gap-2">
                      {selectedTask.media_urls.map((_, index) => (
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