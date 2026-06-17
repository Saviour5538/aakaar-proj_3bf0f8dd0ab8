import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, 
  FileSpreadsheet, 
  Upload, 
  Users, 
  Database, 
  Activity,
  Clock,
  ArrowUpRight,
  FileText,
  UserCheck
} from 'lucide-react';

interface DashboardStats {
  totalSessions: number;
  totalUploads: number;
  totalUsers: number;
  activeSessions: number;
}

interface RecentItem {
  id: string;
  type: 'session' | 'upload' | 'user';
  title: string;
  description: string;
  timestamp: string;
  status?: 'active' | 'completed' | 'pending';
}

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalSessions: 0,
    totalUploads: 0,
    totalUsers: 0,
    activeSessions: 0
  });
  const [recentItems, setRecentItems] = useState<RecentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch stats from API
        const statsResponse = await fetch('/api/dashboard/stats');
        const statsData = await statsResponse.json();
        setStats(statsData);

        // Fetch recent items
        const recentResponse = await fetch('/api/dashboard/recent');
        const recentData = await recentResponse.json();
        setRecentItems(recentData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const statCards = [
    {
      title: 'Total Sessions',
      value: stats.totalSessions,
      icon: <Database className="h-6 w-6" />,
      color: 'bg-blue-500',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
      link: '/sessions'
    },
    {
      title: 'File Uploads',
      value: stats.totalUploads,
      icon: <FileSpreadsheet className="h-6 w-6" />,
      color: 'bg-green-500',
      textColor: 'text-green-600',
      bgColor: 'bg-green-50',
      link: '/upload'
    },
    {
      title: 'Total Users',
      value: stats.totalUsers,
      icon: <Users className="h-6 w-6" />,
      color: 'bg-purple-500',
      textColor: 'text-purple-600',
      bgColor: 'bg-purple-50',
      link: '/users'
    },
    {
      title: 'Active Sessions',
      value: stats.activeSessions,
      icon: <Activity className="h-6 w-6" />,
      color: 'bg-orange-500',
      textColor: 'text-orange-600',
      bgColor: 'bg-orange-50',
      link: '/sessions?status=active'
    }
  ];

  const quickActions = [
    {
      title: 'Upload Excel File',
      description: 'Upload and process new Excel data',
      icon: <Upload className="h-8 w-8" />,
      link: '/upload',
      color: 'bg-blue-100 hover:bg-blue-200',
      iconColor: 'text-blue-600'
    },
    {
      title: 'Start New Session',
      description: 'Begin a new RAG session',
      icon: <BarChart3 className="h-8 w-8" />,
      link: '/sessions/new',
      color: 'bg-green-100 hover:bg-green-200',
      iconColor: 'text-green-600'
    },
    {
      title: 'View Analytics',
      description: 'System performance and usage',
      icon: <Activity className="h-8 w-8" />,
      link: '/analytics',
      color: 'bg-purple-100 hover:bg-purple-200',
      iconColor: 'text-purple-600'
    },
    {
      title: 'Manage Users',
      description: 'User administration and permissions',
      icon: <UserCheck className="h-8 w-8" />,
      link: '/users',
      color: 'bg-orange-100 hover:bg-orange-200',
      iconColor: 'text-orange-600'
    }
  ];

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'active':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Active</span>;
      case 'completed':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">Completed</span>;
      case 'pending':
        return <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">Pending</span>;
      default:
        return null;
    }
  };

  const getItemIcon = (type: string) => {
    switch (type) {
      case 'session':
        return <Database className="h-5 w-5 text-blue-500" />;
      case 'upload':
        return <FileSpreadsheet className="h-5 w-5 text-green-500" />;
      case 'user':
        return <Users className="h-5 w-5 text-purple-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-white rounded-lg shadow p-6">
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/4"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Overview of your Agentic Graph RAG System
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((card, index) => (
            <Link
              key={index}
              to={card.link}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow duration-200"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-lg ${card.bgColor}`}>
                    <div className={card.textColor}>{card.icon}</div>
                  </div>
                  <ArrowUpRight className="h-5 w-5 text-gray-400" />
                </div>
                <h3 className="text-sm font-medium text-gray-600">{card.title}</h3>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {card.value.toLocaleString()}
                </p>
              </div>
            </Link>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Quick Actions</h2>
                <p className="text-gray-600 text-sm mt-1">
                  Common tasks to get started
                </p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {quickActions.map((action, index) => (
                    <Link
                      key={index}
                      to={action.link}
                      className={`${action.color} rounded-lg p-6 transition-all duration-200 hover:scale-[1.02]`}
                    >
                      <div className="flex items-start space-x-4">
                        <div className={`p-3 rounded-lg ${action.iconColor} bg-white`}>
                          {action.icon}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{action.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow h-full">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Recent Activity</h2>
                    <p className="text-gray-600 text-sm mt-1">
                      Latest system interactions
                    </p>
                  </div>
                  <Clock className="h-5 w-5 text-gray-400" />
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {recentItems.length > 0 ? (
                    recentItems.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors duration-150"
                      >
                        <div className="flex-shrink-0 mt-1">
                          {getItemIcon(item.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {item.title}
                            </p>
                            {getStatusBadge(item.status)}
                          </div>
                          <p className="text-sm text-gray-600 mt-1 truncate">
                            {item.description}
                          </p>
                          <div className="flex items-center mt-2">
                            <Clock className="h-3 w-3 text-gray-400 mr-1" />
                            <span className="text-xs text-gray-500">
                              {item.timestamp}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                      <p className="text-gray-500">No recent activity</p>
                    </div>
                  )}
                </div>
                {recentItems.length > 0 && (
                  <div className="mt-6">
                    <Link
                      to="/activity"
                      className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center"
                    >
                      View all activity
                      <ArrowUpRight className="h-4 w-4 ml-1" />
                    </Link>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="mt-8 bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">System Status</h2>
            <p className="text-gray-600 text-sm mt-1">
              Current health and performance metrics
            </p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Chunking Strategy</span>
                  <div className="h-2 w-2 rounded-full bg-green-500"></div>
                </div>
                <p className="text-2xl font-bold text-gray-900">Overlapping</p>
                <p className="text-sm text-gray-600 mt-1">Active and optimized</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Database</span>
                  <div className="h-2 w-2 rounded-full bg-green-500"></div>
                </div>
                <p className="text-2xl font-bold text-gray-900">Connected</p>
                <p className="text-sm text-gray-600 mt-1">Session management active</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">RAG Processing</span>
                  <div className="h-2 w-2 rounded-full bg-green-500"></div>
                </div>
                <p className="text-2xl font-bold text-gray-900">Operational</p>
                <p className="text-sm text-gray-600 mt-1">Agentic graph ready</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;