// Core types for the ChatSEO platform

export interface User {
  id: string;
  email: string;
  plan_type: 'starter' | 'professional' | 'enterprise';
  created_at: string;
  updated_at: string;
}

export interface Brand {
  id: string;
  name: string;
  aliases: string[];
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface MonitoringSession {
  id: string;
  user_id: string;
  brand_names: string[];
  category: string;
  competitors: string[];
  include_reddit: boolean;
  include_chatgpt: boolean;
  include_claude: boolean;
  include_gemini: boolean;
  include_review_sites: boolean;
  time_range: string;
  status: 'running' | 'completed' | 'failed';
  progress_percentage: number;
  current_task: string;
  created_at: string;
  completed_at?: string;
}

export interface MonitoringResults {
  session_id: string;
  brands: string[];
  chatgpt_results?: any;
  claude_results?: any;
  gemini_results?: any;
  reddit_results?: any;
  review_sites_results?: any;
  combined_analytics: CombinedAnalytics;
  recommendations: string[];
  monitoring_duration: number;
  total_mentions: number;
  completed_at: string;
}

export interface CombinedAnalytics {
  summary: {
    total_chatgpt_mentions: number;
    total_claude_mentions: number;
    total_gemini_mentions: number;
    total_reddit_mentions: number;
    total_review_sites_mentions: number;
    combined_mentions: number;
    brands_with_mentions: number;
    reddit_chatgpt_correlation: string;
    review_sites_roi: string;
  };
  brand_breakdown: {
    [brandName: string]: {
      chatgpt_mentions: number;
      claude_mentions: number;
      gemini_mentions: number;
      reddit_mentions: number;
      review_sites_mentions: number;
      combined_mentions: number;
      chatgpt_sentiment: number;
      claude_sentiment: number;
      gemini_sentiment: number;
      reddit_sentiment: number;
      review_sites_sentiment: number;
      average_sentiment: number;
    };
  };
  insights: string[];
}

export interface Citation {
  id: string;
  query_result_id: string;
  brand_name: string;
  mentioned: boolean;
  position?: number;
  context: string;
  sentence: string;
  sentiment_score?: number;
  prominence_score?: number;
  confidence_score: number;
  entity_type: string;
  created_at: string;
}

export interface ReviewSiteMention {
  id: string;
  review_site_name: string;
  brand_name: string;
  mention_url: string;
  mention_title: string;
  mention_content: string;
  rating?: number;
  review_date: string;
  author: string;
  sentiment_score: number;
  ai_citation_potential: number;
  discovered_at: string;
  mention_type: string;
}

export interface RedditMention {
  id: string;
  brand_name: string;
  subreddit: string;
  post_id: string;
  title: string;
  content: string;
  url: string;
  score: number;
  created_utc: string;
  author: string;
  mention_context: string;
  sentiment_score?: number;
  upvotes: number;
  is_post: boolean;
}

export interface MonitoringRequest {
  brand_names: string[];
  category: string;
  competitors?: string[];
  include_reddit?: boolean;
  include_chatgpt?: boolean;
  include_claude?: boolean;
  include_gemini?: boolean;
  include_review_sites?: boolean;
  time_range?: string;
}

export interface MonitoringResponse {
  session_id: string;
  user_id: string;
  brands_monitored: string[];
  monitoring_started: string;
  estimated_completion: string;
  status: string;
  message: string;
}

export interface MonitoringStatus {
  session_id: string;
  status: string;
  progress_percentage: number;
  current_task: string;
  results_summary?: any;
  error_message?: string;
}

export interface DashboardStats {
  total_mentions: number;
  active_sessions: number;
  brands_monitored: number;
  avg_sentiment: number;
  platform_breakdown: {
    chatgpt: number;
    claude: number;
    gemini: number;
    reddit: number;
    review_sites: number;
  };
  recent_mentions: Citation[];
  top_brands: {
    name: string;
    mentions: number;
    sentiment: number;
  }[];
}

export interface ROIMetrics {
  investment_cost: number;
  mentions_found: number;
  ai_citation_frequency: number;
  estimated_ai_citation_value: number;
  roi_percentage: number;
  payback_period_months: number;
  authority_score: number;
  recommendation: string;
}

export interface CompetitorAnalysis {
  brand_name: string;
  competitor_name: string;
  mention_comparison: {
    brand_mentions: number;
    competitor_mentions: number;
    sentiment_comparison: {
      brand_sentiment: number;
      competitor_sentiment: number;
    };
  };
  platform_performance: {
    [platform: string]: {
      brand_mentions: number;
      competitor_mentions: number;
      brand_sentiment: number;
      competitor_sentiment: number;
    };
  };
  insights: string[];
}

export interface Alert {
  id: string;
  user_id: string;
  type: 'mention' | 'sentiment' | 'competitor' | 'threshold';
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
  read: boolean;
  created_at: string;
  metadata?: any;
}

export interface APIResponse<T> {
  data: T;
  message?: string;
  error?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

export interface FilterOptions {
  platforms?: string[];
  date_range?: {
    start: string;
    end: string;
  };
  sentiment_range?: {
    min: number;
    max: number;
  };
  brands?: string[];
  categories?: string[];
}

export interface ExportOptions {
  format: 'csv' | 'json' | 'pdf';
  data_type: 'mentions' | 'analytics' | 'full_report';
  filters?: FilterOptions;
  include_charts?: boolean;
}

export interface NLPAnalysis {
  entity_name: string;
  entity_type: string;
  confidence: number;
  sentiment_score: number;
  sentiment_confidence: number;
  prominence_score: number;
  authority_score: number;
  context_flags: {
    comparison_context: boolean;
    recommendation_context: boolean;
    negative_context: boolean;
    question_context: boolean;
  };
  semantic_role: string;
  dependency_relation: string;
}