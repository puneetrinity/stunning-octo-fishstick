import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout/Layout';
import Button from '@/components/UI/Button';
import LoadingSpinner from '@/components/UI/LoadingSpinner';
import { useForm } from 'react-hook-form';
import { monitoringAPI } from '@/lib/api';
import { MonitoringRequest, MonitoringResponse, MonitoringStatus } from '@/types';
import { PlayIcon, StopIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface MonitoringForm {
  brand_names: string;
  category: string;
  competitors: string;
  include_reddit: boolean;
  include_chatgpt: boolean;
  include_claude: boolean;
  include_gemini: boolean;
  include_review_sites: boolean;
  time_range: string;
}

const Monitoring = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [currentSession, setCurrentSession] = useState<MonitoringResponse | null>(null);
  const [sessionStatus, setSessionStatus] = useState<MonitoringStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<MonitoringForm>({
    defaultValues: {
      category: 'saas',
      include_reddit: true,
      include_chatgpt: true,
      include_claude: true,
      include_gemini: true,
      include_review_sites: true,
      time_range: 'week'
    }
  });

  const onSubmit = async (data: MonitoringForm) => {
    setLoading(true);
    try {
      const request: MonitoringRequest = {
        brand_names: data.brand_names.split(',').map(name => name.trim()),
        category: data.category,
        competitors: data.competitors ? data.competitors.split(',').map(name => name.trim()) : [],
        include_reddit: data.include_reddit,
        include_chatgpt: data.include_chatgpt,
        include_claude: data.include_claude,
        include_gemini: data.include_gemini,
        include_review_sites: data.include_review_sites,
        time_range: data.time_range
      };

      const response = await monitoringAPI.startMonitoring(request);
      setCurrentSession(response);
      setIsMonitoring(true);
      toast.success('Monitoring started successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start monitoring');
    } finally {
      setLoading(false);
    }
  };

  // Poll for status updates
  useEffect(() => {
    if (!currentSession || !isMonitoring) return;

    const pollStatus = async () => {
      try {
        const status = await monitoringAPI.getMonitoringStatus(currentSession.session_id);
        setSessionStatus(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          setIsMonitoring(false);
          if (status.status === 'completed') {
            toast.success('Monitoring completed successfully!');
          } else {
            toast.error('Monitoring failed: ' + status.error_message);
          }
        }
      } catch (error) {
        console.error('Error polling status:', error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [currentSession, isMonitoring]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <LoadingSpinner size="small" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-success-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-error-500" />;
      default:
        return <PlayIcon className="h-5 w-5 text-secondary-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-warning-600 bg-warning-100';
      case 'completed':
        return 'text-success-600 bg-success-100';
      case 'failed':
        return 'text-error-600 bg-error-100';
      default:
        return 'text-secondary-600 bg-secondary-100';
    }
  };

  return (
    <Layout 
      title="Brand Monitoring" 
      subtitle="Monitor your brand mentions across AI platforms and social media"
    >
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Monitoring Form */}
        <div className="bg-white rounded-lg shadow-elevation-1 border border-secondary-200">
          <div className="px-6 py-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">
              Start New Monitoring Session
            </h2>
            <p className="text-sm text-secondary-600 mt-1">
              Configure your brand monitoring across multiple AI platforms
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">
                  Brand Names *
                </label>
                <input
                  {...register('brand_names', { required: 'Brand names are required' })}
                  type="text"
                  className="input"
                  placeholder="e.g., Acme Corp, AcmeSoft"
                  disabled={isMonitoring}
                />
                <p className="text-xs text-secondary-500 mt-1">
                  Comma-separated list of brand names to monitor
                </p>
                {errors.brand_names && (
                  <p className="form-error">{errors.brand_names.message}</p>
                )}
              </div>

              <div>
                <label className="label">
                  Category *
                </label>
                <select
                  {...register('category', { required: 'Category is required' })}
                  className="input"
                  disabled={isMonitoring}
                >
                  <option value="saas">SaaS</option>
                  <option value="b2b">B2B</option>
                  <option value="tech">Technology</option>
                  <option value="fintech">FinTech</option>
                  <option value="martech">MarTech</option>
                </select>
                {errors.category && (
                  <p className="form-error">{errors.category.message}</p>
                )}
              </div>

              <div>
                <label className="label">
                  Competitors (Optional)
                </label>
                <input
                  {...register('competitors')}
                  type="text"
                  className="input"
                  placeholder="e.g., CompetitorA, CompetitorB"
                  disabled={isMonitoring}
                />
                <p className="text-xs text-secondary-500 mt-1">
                  Comma-separated list of competitor names
                </p>
              </div>

              <div>
                <label className="label">
                  Time Range (Reddit)
                </label>
                <select
                  {...register('time_range')}
                  className="input"
                  disabled={isMonitoring}
                >
                  <option value="hour">Last Hour</option>
                  <option value="day">Last Day</option>
                  <option value="week">Last Week</option>
                  <option value="month">Last Month</option>
                  <option value="year">Last Year</option>
                </select>
              </div>
            </div>

            {/* Platform Selection */}
            <div>
              <label className="label mb-3">
                Platforms to Monitor
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-3">
                  <input
                    {...register('include_chatgpt')}
                    type="checkbox"
                    id="chatgpt"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                    disabled={isMonitoring}
                  />
                  <label htmlFor="chatgpt" className="text-sm font-medium text-secondary-700">
                    ChatGPT (OpenAI)
                  </label>
                </div>

                <div className="flex items-center space-x-3">
                  <input
                    {...register('include_claude')}
                    type="checkbox"
                    id="claude"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                    disabled={isMonitoring}
                  />
                  <label htmlFor="claude" className="text-sm font-medium text-secondary-700">
                    Claude (Anthropic)
                  </label>
                </div>

                <div className="flex items-center space-x-3">
                  <input
                    {...register('include_gemini')}
                    type="checkbox"
                    id="gemini"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                    disabled={isMonitoring}
                  />
                  <label htmlFor="gemini" className="text-sm font-medium text-secondary-700">
                    Gemini (Google)
                  </label>
                </div>

                <div className="flex items-center space-x-3">
                  <input
                    {...register('include_reddit')}
                    type="checkbox"
                    id="reddit"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                    disabled={isMonitoring}
                  />
                  <label htmlFor="reddit" className="text-sm font-medium text-secondary-700">
                    Reddit (6% of ChatGPT sources)
                  </label>
                </div>

                <div className="flex items-center space-x-3">
                  <input
                    {...register('include_review_sites')}
                    type="checkbox"
                    id="review_sites"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                    disabled={isMonitoring}
                  />
                  <label htmlFor="review_sites" className="text-sm font-medium text-secondary-700">
                    Review Sites (G2, Capterra, etc.)
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                loading={loading}
                disabled={isMonitoring}
                className="w-full md:w-auto"
              >
                {isMonitoring ? 'Monitoring in Progress...' : 'Start Monitoring'}
              </Button>
            </div>
          </form>
        </div>

        {/* Current Session Status */}
        {currentSession && (
          <div className="bg-white rounded-lg shadow-elevation-1 border border-secondary-200">
            <div className="px-6 py-4 border-b border-secondary-200">
              <h2 className="text-lg font-semibold text-secondary-900">
                Current Session
              </h2>
              <p className="text-sm text-secondary-600 mt-1">
                Session ID: {currentSession.session_id}
              </p>
            </div>

            <div className="p-6">
              {sessionStatus && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(sessionStatus.status)}
                      <span className="font-medium text-secondary-900">
                        {sessionStatus.current_task}
                      </span>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(sessionStatus.status)}`}>
                      {sessionStatus.status.charAt(0).toUpperCase() + sessionStatus.status.slice(1)}
                    </span>
                  </div>

                  <div className="w-full bg-secondary-200 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${sessionStatus.progress_percentage}%` }}
                    />
                  </div>

                  <div className="text-sm text-secondary-600">
                    Progress: {sessionStatus.progress_percentage.toFixed(1)}%
                  </div>

                  {sessionStatus.status === 'completed' && (
                    <div className="bg-success-50 border border-success-200 rounded-lg p-4">
                      <p className="text-success-800 font-medium">
                        Monitoring completed successfully!
                      </p>
                      <Button
                        variant="success"
                        size="small"
                        className="mt-2"
                        onClick={() => window.location.href = `/monitoring/results/${currentSession.session_id}`}
                      >
                        View Results
                      </Button>
                    </div>
                  )}

                  {sessionStatus.status === 'failed' && (
                    <div className="bg-error-50 border border-error-200 rounded-lg p-4">
                      <p className="text-error-800 font-medium">
                        Monitoring failed
                      </p>
                      {sessionStatus.error_message && (
                        <p className="text-error-600 text-sm mt-1">
                          {sessionStatus.error_message}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Monitoring;