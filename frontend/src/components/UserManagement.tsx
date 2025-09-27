import React, { useState, useEffect } from 'react';
import { userManagementApi, adminApi } from '../api';
import type {
  Role,
  PositionHolder,
  CreateRoleRequest,
  CreateUserWithPositionRequest,
  UpdatePositionHolderRequest,
  District,
  Block,
  Village,
  User,
} from '../types';

interface UserManagementProps {
  currentUser: User;
}

const UserManagement: React.FC<UserManagementProps> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState<'roles' | 'users'>('users');
  const [roles, setRoles] = useState<Role[]>([]);
  const [positionHolders, setPositionHolders] = useState<PositionHolder[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [villages, setVillages] = useState<Village[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [showCreateRoleForm, setShowCreateRoleForm] = useState(false);
  const [showCreateUserForm, setShowCreateUserForm] = useState(false);
  const [editingPosition, setEditingPosition] = useState<PositionHolder | null>(null);

  // Form data
  const [roleFormData, setRoleFormData] = useState<CreateRoleRequest>({
    name: '',
    description: undefined,
  });

  const [userFormData, setUserFormData] = useState<CreateUserWithPositionRequest>({
    role_name: '',
    first_name: '',
    last_name: '',
    middle_name: undefined,
    date_of_joining: undefined,
    district_id: undefined,
    block_id: undefined,
    village_id: undefined,
    contractor_name: undefined,
    password: undefined,
    start_date: undefined,
    end_date: undefined,
  });

  const [editFormData, setEditFormData] = useState<UpdatePositionHolderRequest>({});

  // Password change states
  const [showPasswordChangeForm, setShowPasswordChangeForm] = useState(false);
  const [passwordChangeUserId, setPasswordChangeUserId] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const isAdmin = currentUser?.roles?.includes('ADMIN');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rolesData, positionHoldersData, districtsData] = await Promise.all([
        userManagementApi.getAllRoles(),
        userManagementApi.getAllPositionHolders(),
        adminApi.getDistricts(),
      ]);
      setRoles(rolesData);
      setPositionHolders(positionHoldersData);
      setDistricts(districtsData);
    } catch (err: unknown) {
      let errorMessage = 'Failed to load data';
      if (err instanceof Error && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const loadBlocks = async (districtId: number) => {
    try {
      const blocksData = await adminApi.getBlocks(districtId);
      setBlocks(blocksData);
    } catch (err) {
      console.error('Failed to load blocks:', err);
    }
  };

  const loadVillages = async (blockId: number) => {
    try {
      const villagesData = await adminApi.getVillages(blockId);
      setVillages(villagesData);
    } catch (err) {
      console.error('Failed to load villages:', err);
    }
  };

  const handleCreateRole = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await userManagementApi.createRole(roleFormData);
      setShowCreateRoleForm(false);
      setRoleFormData({ name: '', description: '' });
      await loadData();
    } catch (err: unknown) {
      let errorMessage = 'Failed to create role';
      if (err instanceof Error && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await userManagementApi.createUserWithPosition(userFormData);
      setShowCreateUserForm(false);
      setUserFormData({
        role_name: '',
        first_name: '',
        last_name: '',
        middle_name: undefined,
        date_of_joining: undefined,
        district_id: undefined,
        block_id: undefined,
        village_id: undefined,
        contractor_name: undefined,
        password: undefined,
        start_date: undefined,
        end_date: undefined,
      });
      await loadData();
    } catch (err: unknown) {
      let errorMessage = 'Failed to create user';
      if (err instanceof Error && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleEditPosition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPosition) return;

    setLoading(true);
    try {
      await userManagementApi.updatePositionHolder(editingPosition.id, editFormData);
      setEditingPosition(null);
      setEditFormData({});
      await loadData();
    } catch (err: unknown) {
      let errorMessage = 'Failed to update position';
      if (err instanceof Error && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }  
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (position: PositionHolder) => {
    setEditingPosition(position);
    setEditFormData({
      first_name: position.first_name,
      middle_name: position.middle_name,
      last_name: position.last_name,
      date_of_joining: position.date_of_joining,
      start_date: position.start_date,
      end_date: position.end_date,
    });
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passwordChangeUserId) return;
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await userManagementApi.changeUserPassword(passwordChangeUserId, { new_password: newPassword });
      setShowPasswordChangeForm(false);
      setPasswordChangeUserId(null);
      setNewPassword('');
      setConfirmPassword('');
      // You could show a success message here
    } catch (err: unknown) {
      let errorMessage = 'Failed to change password';
      if (err instanceof Error && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const startPasswordChange = (userId: number) => {
    setPasswordChangeUserId(userId);
    setShowPasswordChangeForm(true);
    setNewPassword('');
    setConfirmPassword('');
    setError(null);
  };

  if (loading && !positionHolders.length) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">User Management</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 font-medium rounded-lg ${activeTab === 'users'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
        >
          Users & Position Holders
        </button>
        {isAdmin && (
          <button
            onClick={() => setActiveTab('roles')}
            className={`px-4 py-2 font-medium rounded-lg ${activeTab === 'roles'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
          >
            Roles Management
          </button>
        )}
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Position Holders</h2>
            {(isAdmin || currentUser?.roles?.includes('CEO')) && (
              <button
                onClick={() => setShowCreateUserForm(true)}
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600"
              >
                Create New User
              </button>
            )}
          </div>

          {/* Position Holders Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Username
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joining Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {positionHolders.map((position) => (
                  <tr key={position.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {position.first_name} {position.middle_name} {position.last_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {position.role_name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.village_name && `${position.village_name}, `}
                      {position.block_name && `${position.block_name}, `}
                      {position.district_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.username}
                    </td>
                    {/* <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.date_of_joining || 'Not set'}
                    </td> */}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => startEdit(position)}
                        className="text-indigo-600 hover:text-indigo-900 mr-4"
                      >
                        Edit
                      </button>
                      {isAdmin && (
                        <button
                          onClick={() => startPasswordChange(position.user_id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          Change Password
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Roles Tab */}
      {activeTab === 'roles' && isAdmin && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">Roles</h2>
            <button
              onClick={() => setShowCreateRoleForm(true)}
              className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600"
            >
              Create New Role
            </button>
          </div>

          {/* Roles Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {roles.map((role) => (
                  <tr key={role.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {role.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {role.description || 'No description'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Role Modal */}
      {showCreateRoleForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Create New Role</h3>
            <form onSubmit={handleCreateRole}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={roleFormData.name}
                  onChange={(e) => setRoleFormData({ ...roleFormData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={roleFormData.description || ''}
                  onChange={(e) => setRoleFormData({ ...roleFormData, description: e.target.value || undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  rows={3}
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCreateRoleForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Role'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUserForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Create New User</h3>
            <form onSubmit={handleCreateUser} className="grid grid-cols-2 gap-4">
              {/* Role Selection */}
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700">Role</label>
                <select
                  value={userFormData.role_name}
                  onChange={(e) => setUserFormData({ ...userFormData, role_name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                >
                  <option value="">Select Role</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.name}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Personal Information */}
              <div>
                <label className="block text-sm font-medium text-gray-700">First Name</label>
                <input
                  type="text"
                  value={userFormData.first_name}
                  onChange={(e) => setUserFormData({ ...userFormData, first_name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Last Name</label>
                <input
                  type="text"
                  value={userFormData.last_name}
                  onChange={(e) => setUserFormData({ ...userFormData, last_name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Middle Name</label>
                <input
                  type="text"
                  value={userFormData.middle_name || ''}
                  onChange={(e) => setUserFormData({ ...userFormData, middle_name: e.target.value || undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Date of Joining</label>
                <input
                  type="date"
                  value={userFormData.date_of_joining ? (typeof userFormData.date_of_joining === 'string' ? userFormData.date_of_joining : userFormData.date_of_joining.toISOString().split('T')[0]) : ''}
                  onChange={(e) => setUserFormData({ ...userFormData, date_of_joining: e.target.value ? new Date(e.target.value) : undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              {/* Geographic Assignment */}
              <div>
                <label className="block text-sm font-medium text-gray-700">District</label>
                <select
                  value={userFormData.district_id || ''}
                  onChange={(e) => {
                    const districtId = e.target.value ? parseInt(e.target.value) : undefined;
                    setUserFormData({ ...userFormData, district_id: districtId, block_id: undefined, village_id: undefined });
                    if (districtId) loadBlocks(districtId);
                  }}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="">Select District</option>
                  {districts.map((district) => (
                    <option key={district.id} value={district.id}>
                      {district.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Block</label>
                <select
                  value={userFormData.block_id || ''}
                  onChange={(e) => {
                    const blockId = e.target.value ? parseInt(e.target.value) : undefined;
                    setUserFormData({ ...userFormData, block_id: blockId, village_id: undefined });
                    if (blockId) loadVillages(blockId);
                  }}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  disabled={!userFormData.district_id}
                >
                  <option value="">Select Block</option>
                  {blocks.map((block) => (
                    <option key={block.id} value={block.id}>
                      {block.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Village</label>
                <select
                  value={userFormData.village_id || ''}
                  onChange={(e) => setUserFormData({ ...userFormData, village_id: e.target.value ? parseInt(e.target.value) : undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  disabled={!userFormData.block_id}
                >
                  <option value="">Select Village</option>
                  {villages.map((village) => (
                    <option key={village.id} value={village.id}>
                      {village.name}
                    </option>
                  ))}
                </select>
              </div>
              {userFormData.role_name === 'WORKER' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Contractor Name</label>
                  <input
                    type="text"
                    value={userFormData.contractor_name || ''}
                    onChange={(e) => setUserFormData({ ...userFormData, contractor_name: e.target.value || undefined })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    placeholder="For worker role username generation"
                  />
                </div>
              )}

              {/* Dates */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Start Date</label>
                <input
                  type="date"
                  value={userFormData.start_date ? (typeof userFormData.start_date === 'string' ? userFormData.start_date : userFormData.start_date.toISOString().split('T')[0]) : ''}
                  onChange={(e) => setUserFormData({ ...userFormData, start_date: e.target.value ? new Date(e.target.value) : undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">End Date</label>
                <input
                  type="date"
                  value={userFormData.end_date ? (typeof userFormData.end_date === 'string' ? userFormData.end_date : userFormData.end_date.toISOString().split('T')[0]) : ''}
                  onChange={(e) => setUserFormData({ ...userFormData, end_date: e.target.value ? new Date(e.target.value) : undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700">Password (optional)</label>
                <input
                  type="password"
                  value={userFormData.password || ''}
                  onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value || undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  placeholder="Leave blank for default password"
                />
              </div>

              <div className="col-span-2 flex justify-end space-x-2 mt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateUserForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Position Modal */}
      {editingPosition && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Edit Position Holder</h3>
            <form onSubmit={handleEditPosition}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">First Name</label>
                <input
                  type="text"
                  value={editFormData.first_name || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, first_name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  disabled={!isAdmin}
                />
                {!isAdmin && <p className="text-xs text-gray-500 mt-1">Only admins can edit names</p>}
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Middle Name</label>
                <input
                  type="text"
                  value={editFormData.middle_name || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, middle_name: e.target.value || undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  disabled={!isAdmin}
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Last Name</label>
                <input
                  type="text"
                  value={editFormData.last_name || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, last_name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  disabled={!isAdmin}
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Date of Joining</label>
                <input
                  type="date"
                  value={editFormData.date_of_joining ? (typeof editFormData.date_of_joining === 'string' ? editFormData.date_of_joining : editFormData.date_of_joining.toISOString().split('T')[0]) : ''}
                  onChange={(e) => setEditFormData({ ...editFormData, date_of_joining: e.target.value ? new Date(e.target.value) : undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  disabled={!isAdmin}
                />
                {!isAdmin && <p className="text-xs text-gray-500 mt-1">Only admins can edit date of joining</p>}
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Start Date</label>
                <input
                  type="date"
                  value={editFormData.start_date ? (typeof editFormData.start_date === 'string' ? editFormData.start_date : editFormData.start_date.toISOString().split('T')[0]) : ''}
                  onChange={(e) => setEditFormData({ ...editFormData, start_date: e.target.value ? new Date(e.target.value) : undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">End Date</label>
                <input
                  type="date"
                  value={editFormData.end_date ? (typeof editFormData.end_date === 'string' ? editFormData.end_date : editFormData.end_date.toISOString().split('T')[0]) : ''}
                  onChange={(e) => setEditFormData({ ...editFormData, end_date: e.target.value ? new Date(e.target.value) : undefined })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setEditingPosition(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update Position'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Password Change Modal */}
      {showPasswordChangeForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Change User Password</h3>
            <form onSubmit={handlePasswordChange}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                  minLength={8}
                  placeholder="Enter new password (min 8 characters)"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  required
                  minLength={8}
                  placeholder="Confirm new password"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordChangeForm(false);
                    setPasswordChangeUserId(null);
                    setNewPassword('');
                    setConfirmPassword('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || newPassword !== confirmPassword || newPassword.length < 8}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;