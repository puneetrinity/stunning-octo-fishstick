"""
Pricing configuration for dual-market approach
"""
from typing import Dict, List, Any


class PricingConfig:
    """Pricing configuration for both agency and brand tiers"""
    
    BRAND_TIERS = {
        'brand_starter': {
            'price_usd': 199,
            'price_cents': 19900,
            'target_market': 'Small-medium businesses',
            'description': 'Essential brand monitoring and competitor analysis',
            'limits': {
                'brands_tracked': 5,
                'queries_per_month': 1000,
                'platforms': ['openai', 'anthropic', 'google'],
                'team_members': 2,
                'api_calls': 1000,
                'reports_per_month': 4
            },
            'features': [
                'brand_monitoring',
                'competitor_analysis',
                'basic_reports',
                'email_alerts',
                'dashboard_access'
            ]
        },
        'brand_professional': {
            'price_usd': 399,
            'price_cents': 39900,
            'target_market': 'Enterprise brands',
            'description': 'Advanced analytics and content recommendations',
            'limits': {
                'brands_tracked': 15,
                'queries_per_month': 3000,
                'platforms': ['all'],
                'team_members': 5,
                'api_calls': 3000,
                'reports_per_month': 12
            },
            'features': [
                'advanced_analytics',
                'content_recommendations',
                'api_access',
                'custom_reports',
                'priority_support',
                'sentiment_analysis',
                'competitor_intelligence'
            ]
        }
    }
    
    AGENCY_TIERS = {
        'agency_starter': {
            'price_usd': 299,
            'price_cents': 29900,
            'target_market': 'Small agencies (3-5 clients)',
            'description': 'Multi-client dashboard with ROI tracking',
            'limits': {
                'clients': 5,
                'brands_per_client': 10,
                'queries_per_month': 1500,
                'review_sites': ['g2', 'capterra', 'trustradius'],
                'team_members': 3,
                'reports_per_month': 20
            },
            'features': [
                'multi_client_dashboard',
                'roi_tracking',
                'basic_reports',
                'review_site_monitoring',
                'client_management',
                'email_alerts'
            ]
        },
        'agency_pro': {
            'price_usd': 599,
            'price_cents': 59900,
            'target_market': 'Medium agencies (10-15 clients)',
            'description': 'White-label reports and advanced analytics',
            'limits': {
                'clients': 15,
                'brands_per_client': 20,
                'queries_per_month': 5000,
                'review_sites': ['all_major_sites'],
                'team_members': 8,
                'reports_per_month': 60
            },
            'features': [
                'white_label_reports',
                'advanced_analytics',
                'api_access',
                'content_gap_analysis',
                'competitor_tracking',
                'roi_modeling',
                'custom_dashboards',
                'priority_support'
            ]
        },
        'agency_enterprise': {
            'price_usd': 1299,
            'price_cents': 129900,
            'target_market': 'Large agencies (25+ clients)',
            'description': 'Full-featured platform with custom integrations',
            'limits': {
                'clients': 999,  # Effectively unlimited
                'brands_per_client': 50,
                'queries_per_month': 20000,
                'review_sites': ['all_sites_plus_custom'],
                'team_members': 999,  # Effectively unlimited
                'reports_per_month': 999  # Effectively unlimited
            },
            'features': [
                'custom_integrations',
                'dedicated_support',
                'advanced_roi_modeling',
                'enterprise_sla',
                'custom_training',
                'api_priority',
                'custom_features',
                'account_manager'
            ]
        }
    }
    
    @classmethod
    def get_plan_config(cls, plan_type: str) -> Dict[str, Any]:
        """Get configuration for a specific plan"""
        if plan_type.startswith('brand_'):
            return cls.BRAND_TIERS.get(plan_type, {})
        elif plan_type.startswith('agency_'):
            return cls.AGENCY_TIERS.get(plan_type, {})
        return {}
    
    @classmethod
    def get_all_plans(cls) -> Dict[str, Dict[str, Any]]:
        """Get all plan configurations"""
        return {**cls.BRAND_TIERS, **cls.AGENCY_TIERS}
    
    @classmethod
    def get_brand_plans(cls) -> Dict[str, Dict[str, Any]]:
        """Get brand-specific plans"""
        return cls.BRAND_TIERS
    
    @classmethod
    def get_agency_plans(cls) -> Dict[str, Dict[str, Any]]:
        """Get agency-specific plans"""
        return cls.AGENCY_TIERS
    
    @classmethod
    def is_feature_available(cls, plan_type: str, feature: str) -> bool:
        """Check if a feature is available for a plan"""
        config = cls.get_plan_config(plan_type)
        return feature in config.get('features', [])
    
    @classmethod
    def get_plan_limit(cls, plan_type: str, limit_type: str) -> int:
        """Get specific limit for a plan"""
        config = cls.get_plan_config(plan_type)
        return config.get('limits', {}).get(limit_type, 0)
    
    @classmethod
    def can_upgrade_to(cls, current_plan: str, target_plan: str) -> bool:
        """Check if user can upgrade from current plan to target plan"""
        current_config = cls.get_plan_config(current_plan)
        target_config = cls.get_plan_config(target_plan)
        
        if not current_config or not target_config:
            return False
        
        # Can upgrade within same tier type (brand to brand, agency to agency)
        current_type = 'brand' if current_plan.startswith('brand_') else 'agency'
        target_type = 'brand' if target_plan.startswith('brand_') else 'agency'
        
        if current_type != target_type:
            return False
        
        # Can upgrade to higher price tier
        return target_config['price_cents'] > current_config['price_cents']


# Common review sites configuration
REVIEW_SITES = {
    'g2': {
        'name': 'G2',
        'domain': 'g2.com',
        'category': 'software',
        'authority_score': 95,
        'average_cost_per_review': 2500.00,
        'ai_citation_frequency': 0.85
    },
    'capterra': {
        'name': 'Capterra',
        'domain': 'capterra.com',
        'category': 'software',
        'authority_score': 90,
        'average_cost_per_review': 2000.00,
        'ai_citation_frequency': 0.78
    },
    'trustradius': {
        'name': 'TrustRadius',
        'domain': 'trustradius.com',
        'category': 'software',
        'authority_score': 85,
        'average_cost_per_review': 1800.00,
        'ai_citation_frequency': 0.72
    },
    'gartner': {
        'name': 'Gartner',
        'domain': 'gartner.com',
        'category': 'enterprise',
        'authority_score': 98,
        'average_cost_per_review': 10000.00,
        'ai_citation_frequency': 0.95
    },
    'forrester': {
        'name': 'Forrester',
        'domain': 'forrester.com',
        'category': 'enterprise',
        'authority_score': 96,
        'average_cost_per_review': 8000.00,
        'ai_citation_frequency': 0.92
    }
}

# Authority sources by industry
AUTHORITY_SOURCES = {
    'saas': [
        {'name': 'SaaS Mag', 'domain': 'saasmag.com', 'authority_score': 75},
        {'name': 'SaaS Weekly', 'domain': 'saasweekly.com', 'authority_score': 70},
        {'name': 'Product Hunt', 'domain': 'producthunt.com', 'authority_score': 85}
    ],
    'fintech': [
        {'name': 'Fintech News', 'domain': 'fintechnews.com', 'authority_score': 80},
        {'name': 'Banking Tech', 'domain': 'bankingtech.com', 'authority_score': 85},
        {'name': 'Payments Journal', 'domain': 'paymentsjournal.com', 'authority_score': 75}
    ],
    'martech': [
        {'name': 'MarTech Today', 'domain': 'martechtoday.com', 'authority_score': 90},
        {'name': 'CMSWire', 'domain': 'cmswire.com', 'authority_score': 85},
        {'name': 'Marketing Land', 'domain': 'marketingland.com', 'authority_score': 88}
    ]
}