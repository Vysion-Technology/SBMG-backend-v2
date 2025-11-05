import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Home, FileText, Users, Settings, LogOut, LogIn, UserCheck, User as UserIcon } from 'lucide-react';

// Import components (we'll create these)
import HomePage from './components/HomePage';
import CreateComplaint from './components/CreateComplaint';
import ComplaintStatus from './components/ComplaintStatus';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import WorkerDashboard from './components/WorkerDashboard';
import UserDashboard from './components/UserDashboard';
import AdminPanel from './components/AdminPanel';
import UserManagement from './components/UserManagement';
import CitizenComplaintVerification from './components/CitizenComplaintVerification';
import ComplaintDetailPage from './components/ComplaintDetailPage';
import type { User } from './types';
import { authApi } from './api';
import { getUserHighestRole, userHasAdminPrivileges, userIsWorker } from './utils';

function App() {
  const [user, setUser] = React.useState<User | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Fetch current user info from /me endpoint
            authApi.getCurrentUser()
        .then((userData) => {
          const typedUser = userData as User;
          setUser(typedUser);
          localStorage.setItem('current_user_id', typedUser.id.toString());
        })
        .catch((error) => {
          console.error('Failed to fetch user info:', error);
          // Remove invalid token
          localStorage.removeItem('token');
          localStorage.removeItem('current_user_id');
          setUser(null);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('current_user_id');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <h1 className="text-xl font-bold text-gray-900">
                    SBM Gramin Rajasthan
                  </h1>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <NavLink to="/" icon={<Home size={16} />}>
                    Home
                  </NavLink>
                  <NavLink to="/create-complaint" icon={<FileText size={16} />}>
                    Create Complaint
                  </NavLink>
                  <NavLink to="/complaint-status" icon={<UserCheck size={16} />}>
                    Check Status
                  </NavLink>
                  <NavLink to="/citizen-verification" icon={<UserCheck size={16} />}>
                    Verify Resolution
                  </NavLink>
                  {user && userHasAdminPrivileges(user) && (
                    <NavLink to="/dashboard" icon={<Settings size={16} />}>
                      Admin Dashboard
                    </NavLink>
                  )}
                  {user && userHasAdminPrivileges(user) && (
                    <NavLink to="/admin" icon={<Settings size={16} />}>
                      Admin Panel
                    </NavLink>
                  )}
                  {user && (userHasAdminPrivileges(user) || getUserHighestRole(user) === 'CEO') && (
                    <NavLink to="/user-management" icon={<Users size={16} />}>
                      User Management
                    </NavLink>
                  )}
                  
                  {user && userIsWorker(user) && (
                    <NavLink to="/worker-dashboard" icon={<Users size={16} />}>
                      VDO Dashboard
                    </NavLink>
                  )}
                  {user && !userHasAdminPrivileges(user) && !userIsWorker(user) && (
                    <NavLink to="/user-dashboard" icon={<UserIcon size={16} />}>
                      My Dashboard
                    </NavLink>
                  )}
                </div>
              </div>
              <div className="flex items-center">
                {user ? (
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-700">
                      {user.username} ({getUserHighestRole(user) || 'User'})
                    </span>
                    <button
                      onClick={logout}
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-gray-500 bg-white hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <LogOut size={16} className="mr-2" />
                      Logout
                    </button>
                  </div>
                ) : (
                  <Link
                    to="/login"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <LogIn size={16} className="mr-2" />
                    Login
                  </Link>
                )}
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<HomePage user={user} />} />
            <Route path="/create-complaint" element={<CreateComplaint />} />
            <Route path="/complaint-status" element={<ComplaintStatus />} />
            <Route path="/citizen-verification" element={<CitizenComplaintVerification />} />
            <Route path="/complaint/:id" element={<ComplaintDetailPage />} />
            <Route path="/login" element={<Login setUser={setUser} />} />
            {user && userHasAdminPrivileges(user) && (
              <Route path="/dashboard" element={<Dashboard user={user} />} />
            )}
            {user && userHasAdminPrivileges(user) && (
              <Route path="/admin" element={<AdminPanel user={user} />} />
            )}
            {user && (userHasAdminPrivileges(user) || getUserHighestRole(user) === 'CEO') && (
              <Route path="/user-management" element={<UserManagement currentUser={user} />} />
            )}
            {user && userIsWorker(user) && (
              <Route path="/worker-dashboard" element={<WorkerDashboard user={user} />} />
            )}
            {user && !userHasAdminPrivileges(user) && !userIsWorker(user) && (
              <Route path="/user-dashboard" element={<UserDashboard user={user} />} />
            )}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function NavLink({ to, icon, children }: { to: string; icon: React.ReactNode; children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
        isActive
          ? 'border-indigo-500 text-gray-900'
          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
      }`}
    >
      {icon && <span className="mr-2">{icon}</span>}
      {children}
    </Link>
  );
}

export default App;
