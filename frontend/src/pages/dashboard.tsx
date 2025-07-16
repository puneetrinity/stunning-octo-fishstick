import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout/Layout';
import StatsCard from '@/components/Dashboard/StatsCard';
import LoadingSpinner from '@/components/UI/LoadingSpinner';
import { 
  ChartBarIcon, 
  ChatBubbleLeftRightIcon, 
  GlobeAltIcon, 
  SparklesIcon,
  BuildingOfficeIcon,
  PlayIcon 
} from '@heroicons/react/24/outline';
import { dashboardAPI } from '@/lib/api';
import { DashboardStats } from '@/types';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardAPI.getStats();
        setStats(data);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <Layout title="Dashboard">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="large" />
        </div>
      </Layout>
    );
  }

  if (!stats) {
    return (
      <Layout title="Dashboard">
        <div className="text-center py-12">
          <p className="text-secondary-600">Failed to load dashboard data</p>
        </div>
      </Layout>
    );
  }

  // Mock data for charts
  const sentimentTrend = [
    { name: 'Mon', sentiment: 0.65 },
    { name: 'Tue', sentiment: 0.72 },
    { name: 'Wed', sentiment: 0.68 },
    { name: 'Thu', sentiment: 0.75 },
    { name: 'Fri', sentiment: 0.71 },
    { name: 'Sat', sentiment: 0.69 },
    { name: 'Sun', sentiment: 0.73 },
  ];

  const platformData = [
    { name: 'ChatGPT', mentions: stats.platform_breakdown.chatgpt },
    { name: 'Claude', mentions: stats.platform_breakdown.claude },
    { name: 'Gemini', mentions: stats.platform_breakdown.gemini },
    { name: 'Reddit', mentions: stats.platform_breakdown.reddit },
    { name: 'Review Sites', mentions: stats.platform_breakdown.review_sites },
  ];

  const pieData = [
    { name: 'ChatGPT', value: stats.platform_breakdown.chatgpt, color: '#3b82f6' },
    { name: 'Claude', value: stats.platform_breakdown.claude, color: '#10b981' },
    { name: 'Gemini', value: stats.platform_breakdown.gemini, color: '#f59e0b' },
    { name: 'Reddit', value: stats.platform_breakdown.reddit, color: '#ef4444' },
    { name: 'Review Sites', value: stats.platform_breakdown.review_sites, color: '#8b5cf6' },
  ];

  return (
    <Layout 
      title="Dashboard" 
      subtitle="Monitor your brand mentions across AI platforms"
    >
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard
            title="Total Mentions"
            value={stats.total_mentions.toLocaleString()}
            change={12.5}
            changeType="positive"
            icon={ChartBarIcon}
            description="vs last month"
          />
          <StatsCard
            title="Active Sessions"
            value={stats.active_sessions}
            change={-3.2}
            changeType="negative"
            icon={PlayIcon}
            description="currently running"
          />
          <StatsCard
            title="Brands Monitored"
            value={stats.brands_monitored}
            icon={BuildingOfficeIcon}
          />
          <StatsCard
            title="Avg Sentiment"
            value={`${(stats.avg_sentiment * 100).toFixed(1)}%`}
            change={8.1}
            changeType="positive"
            icon={SparklesIcon}
            description="positive mentions"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sentiment Trend */}
          <div className="bg-white p-6 rounded-lg shadow-elevation-1 border border-secondary-200">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Sentiment Trend
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={sentimentTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 1]} />
                <Tooltip 
                  formatter={(value) => [`${(value as number * 100).toFixed(1)}%`, 'Sentiment']}
                />
                <Line 
                  type="monotone" 
                  dataKey="sentiment" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Platform Distribution */}
          <div className="bg-white p-6 rounded-lg shadow-elevation-1 border border-secondary-200">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Platform Distribution
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Platform Mentions Chart */}
        <div className="bg-white p-6 rounded-lg shadow-elevation-1 border border-secondary-200">
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">
            Mentions by Platform
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={platformData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="mentions" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Mentions */}
          <div className="bg-white p-6 rounded-lg shadow-elevation-1 border border-secondary-200">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Recent Mentions
            </h3>
            <div className="space-y-4">
              {stats.recent_mentions.slice(0, 5).map((mention, index) => (
                <div key={index} className="flex items-center justify-between py-2 border-b border-secondary-100 last:border-b-0">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-secondary-900">
                      {mention.brand_name}
                    </p>
                    <p className="text-sm text-secondary-600 truncate">
                      {mention.context}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      mention.sentiment_score && mention.sentiment_score > 0.6
                        ? 'bg-success-100 text-success-800'
                        : mention.sentiment_score && mention.sentiment_score < 0.4
                        ? 'bg-error-100 text-error-800'
                        : 'bg-secondary-100 text-secondary-800'
                    }`}>
                      {mention.sentiment_score && mention.sentiment_score > 0.6 ? 'Positive' : 
                       mention.sentiment_score && mention.sentiment_score < 0.4 ? 'Negative' : 'Neutral'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Brands */}
          <div className="bg-white p-6 rounded-lg shadow-elevation-1 border border-secondary-200">
            <h3 className="text-lg font-semibold text-secondary-900 mb-4">
              Top Performing Brands
            </h3>
            <div className="space-y-4">
              {stats.top_brands.map((brand, index) => (
                <div key={index} className="flex items-center justify-between py-2">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-primary-600">
                          {brand.name.charAt(0)}
                        </span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-secondary-900">
                        {brand.name}
                      </p>
                      <p className="text-sm text-secondary-600">
                        {brand.mentions} mentions
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      brand.sentiment > 0.6
                        ? 'bg-success-100 text-success-800'
                        : brand.sentiment < 0.4
                        ? 'bg-error-100 text-error-800'
                        : 'bg-secondary-100 text-secondary-800'
                    }`}>
                      {(brand.sentiment * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;