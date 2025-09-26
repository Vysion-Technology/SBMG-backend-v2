import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, AlertCircle } from 'lucide-react';
import { authApi } from '../api';
import type { LoginRequest, User } from '../types';
import { getUserHighestRole } from '../utils';

interface LoginProps {
  setUser: (user: User | null) => void;
}

const Login: React.FC<LoginProps> = ({ setUser }) => {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState<LoginRequest>({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await authApi.login(credentials);
      localStorage.setItem('token', result.access_token);
      
      // Fetch current user data to get role information
      const userData = await authApi.getCurrentUser() as User;
      setUser(userData);
      
      // Navigate based on user role
      if (getUserHighestRole(userData) && ['ADMIN', 'CEO', 'BDO'].includes(getUserHighestRole(userData)!)) {
        navigate('/dashboard');
      } else if (userData.roles.includes('VDO')) {
        navigate('/worker-dashboard');
      } else {
        navigate('/');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      if (error.response?.status === 401) {
        setError('Invalid username or password');
      } else {
        setError('Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-8">
      <div className="bg-white shadow-sm rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 text-center">
          <LogIn size={32} className="mx-auto text-indigo-600 mb-2" />
          <h1 className="text-2xl font-bold text-gray-900">Staff Login</h1>
          <p className="text-gray-600 mt-1">
            Access the dashboard to manage complaints and reports.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter your username"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter your password"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <AlertCircle className="text-red-400 mr-3 mt-0.5" size={20} />
                <p className="text-red-800">{error}</p>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="text-sm text-gray-600">
            <p className="font-medium mb-2">Demo Credentials:</p>
            <div className="space-y-1 text-xs">
              <p><strong>Admin:</strong> admin / admin123</p>
              <p><strong>Worker:</strong> worker1 / worker123</p>
              <p><strong>VDO:</strong> vdo1 / vdo123</p>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              * In production, use your actual credentials provided by the administrator.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;