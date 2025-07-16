# ChatSEO Platform API Examples

This document provides practical examples of how to use the ChatSEO Platform API for both agency and brand users.

## Authentication

### Register as a Brand User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "brand@example.com",
    "password": "SecurePass123",
    "full_name": "John Smith",
    "company_name": "Acme Corp",
    "user_type": "brand",
    "plan_type": "brand_starter"
  }'
```

### Register as an Agency User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "agency@example.com",
    "password": "SecurePass123",
    "full_name": "Jane Doe",
    "company_name": "Digital Marketing Agency",
    "user_type": "agency",
    "plan_type": "agency_starter"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "agency@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

## Brand Management (Both User Types)

### Create a Brand
```bash
curl -X POST "http://localhost:8000/api/v1/brands/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "aliases": ["Acme", "Acme Corporation"],
    "description": "Leading software company",
    "website_url": "https://acme.com",
    "is_primary": true
  }'
```

### List Brands
```bash
curl -X GET "http://localhost:8000/api/v1/brands/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Brand Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/brands/{brand_id}/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "brand_id": "550e8400-e29b-41d4-a716-446655440000",
  "brand_name": "Acme Corp",
  "total_mentions": 42,
  "mention_rate": 67.5,
  "average_prominence": 7.2,
  "average_sentiment": 0.65,
  "platforms": ["openai", "anthropic", "google"],
  "last_mentioned": "2024-01-15T10:30:00Z"
}
```

## Client Management (Agency Users Only)

### Create a Client
```bash
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Startup Inc",
    "company_name": "Tech Startup Inc",
    "website_url": "https://techstartup.com",
    "industry": "SaaS",
    "description": "AI-powered productivity tools",
    "contact_email": "ceo@techstartup.com",
    "contact_name": "Alice Johnson",
    "monthly_budget": "$5K-10K"
  }'
```

### List Clients
```bash
curl -X GET "http://localhost:8000/api/v1/clients/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Assign Brand to Client
```bash
curl -X POST "http://localhost:8000/api/v1/clients/{client_id}/brands" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_primary": true
  }'
```

### Get Client Dashboard
```bash
curl -X GET "http://localhost:8000/api/v1/clients/{client_id}/dashboard" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## ROI Tracking (Agency Users Only)

### Create ROI Investment
```bash
curl -X POST "http://localhost:8000/api/v1/roi/investments" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "investment_type": "review_site",
    "platform": "g2",
    "investment_amount": 2500.00,
    "currency": "USD",
    "investment_date": "2024-01-01T00:00:00Z",
    "description": "G2 premium listing and reviews",
    "expected_roi": 150.0,
    "notes": "Targeting enterprise SaaS category"
  }'
```

### Add Performance Metric
```bash
curl -X POST "http://localhost:8000/api/v1/roi/investments/{investment_id}/metrics" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric_date": "2024-01-15T00:00:00Z",
    "mentions_generated": 12,
    "ai_citations": 8,
    "estimated_traffic": 450,
    "estimated_traffic_value": 1200.00,
    "brand_visibility_score": 7.5,
    "sentiment_score": 0.8,
    "notes": "Strong performance in first two weeks"
  }'
```

### Calculate ROI
```bash
curl -X GET "http://localhost:8000/api/v1/roi/investments/{investment_id}/calculate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "investment_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_investment": 2500.00,
  "current_value": 3200.00,
  "roi_percentage": 28.0,
  "roi_absolute": 700.00,
  "payback_period_days": 45,
  "break_even_date": "2024-02-15T00:00:00Z",
  "performance_trend": "improving"
}
```

### Get ROI Dashboard
```bash
curl -X GET "http://localhost:8000/api/v1/roi/dashboard" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get ROI Dashboard for Specific Client
```bash
curl -X GET "http://localhost:8000/api/v1/roi/dashboard?client_id={client_id}" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Pricing Information

### Get All Pricing Plans
```bash
curl -X GET "http://localhost:8000/api/v1/pricing/" \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "brand_plans": [
    {
      "plan_type": "brand_starter",
      "name": "Small-medium businesses",
      "price_usd": 199,
      "target_market": "Small-medium businesses",
      "description": "Essential brand monitoring and competitor analysis",
      "limits": {
        "brands_tracked": 5,
        "queries_per_month": 1000,
        "platforms": ["openai", "anthropic", "google"],
        "team_members": 2
      },
      "features": [
        "brand_monitoring",
        "competitor_analysis",
        "basic_reports",
        "email_alerts"
      ]
    }
  ],
  "agency_plans": [
    {
      "plan_type": "agency_starter",
      "name": "Small agencies (3-5 clients)",
      "price_usd": 299,
      "target_market": "Small agencies (3-5 clients)",
      "description": "Multi-client dashboard with ROI tracking",
      "limits": {
        "clients": 5,
        "brands_per_client": 10,
        "queries_per_month": 1500
      },
      "features": [
        "multi_client_dashboard",
        "roi_tracking",
        "basic_reports",
        "review_site_monitoring"
      ]
    }
  ]
}
```

### Get Current User's Plan
```bash
curl -X GET "http://localhost:8000/api/v1/pricing/my-plan" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Change Plan
```bash
curl -X POST "http://localhost:8000/api/v1/pricing/change-plan" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_plan_type": "agency_pro"
  }'
```

### Compare Plans
```bash
curl -X GET "http://localhost:8000/api/v1/pricing/compare?current_plan=agency_starter&target_plan=agency_pro" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## User Profile Management

### Get User Profile
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Profile
```bash
curl -X PUT "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith Updated",
    "company_name": "Acme Corp Ltd"
  }'
```

### Change Password
```bash
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123",
    "new_password": "NewSecurePass456"
  }'
```

## Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 403 Forbidden (Agency-only endpoint accessed by brand user)
```json
{
  "detail": "This endpoint is only available to agency users"
}
```

#### 404 Not Found
```json
{
  "detail": "Client not found"
}
```

#### 422 Validation Error
```json
{
  "error": "Validation Error",
  "message": "The request data is invalid",
  "details": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 400 Bad Request (Plan limit exceeded)
```json
{
  "detail": "Client limit reached (5). Upgrade your plan to add more clients."
}
```

## Bulk Operations

### Bulk Create Brands
```bash
curl -X POST "http://localhost:8000/api/v1/brands/bulk" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brands": [
      {
        "name": "Brand One",
        "aliases": ["B1", "Brand1"],
        "description": "First brand",
        "website_url": "https://brand1.com"
      },
      {
        "name": "Brand Two",
        "aliases": ["B2", "Brand2"],
        "description": "Second brand",
        "website_url": "https://brand2.com"
      }
    ]
  }'
```

Response:
```json
{
  "created": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Brand One",
      "aliases": ["B1", "Brand1"],
      "description": "First brand",
      "website_url": "https://brand1.com",
      "is_primary": false,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "failed": [
    {
      "brand_data": {
        "name": "Brand Two",
        "aliases": ["B2", "Brand2"],
        "description": "Second brand",
        "website_url": "https://brand2.com"
      },
      "error": "Brand limit reached (5). Upgrade your plan to add more brands."
    }
  ]
}
```

## JavaScript/TypeScript Examples

### Using fetch in JavaScript
```javascript
// Login
async function login(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  localStorage.setItem('accessToken', data.access_token);
  return data;
}

// Create brand
async function createBrand(brandData) {
  const token = localStorage.getItem('accessToken');
  const response = await fetch('/api/v1/brands/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(brandData),
  });
  
  return await response.json();
}

// Get ROI dashboard (agency only)
async function getROIDashboard(clientId = null) {
  const token = localStorage.getItem('accessToken');
  const url = clientId 
    ? `/api/v1/roi/dashboard?client_id=${clientId}`
    : '/api/v1/roi/dashboard';
    
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  return await response.json();
}
```

### TypeScript Types
```typescript
interface User {
  id: string;
  email: string;
  full_name?: string;
  company_name?: string;
  user_type: 'brand' | 'agency';
  plan_type: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

interface Brand {
  id: string;
  name: string;
  aliases: string[];
  description?: string;
  website_url?: string;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface Client {
  id: string;
  name: string;
  company_name: string;
  website_url?: string;
  industry?: string;
  description?: string;
  contact_email?: string;
  contact_name?: string;
  status: 'active' | 'inactive' | 'suspended';
  monthly_budget?: string;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

interface ROIInvestment {
  id: string;
  client_id: string;
  investment_type: 'review_site' | 'content' | 'advertising' | 'pr' | 'social' | 'other';
  platform: string;
  investment_amount: number;
  currency: string;
  investment_date: string;
  description?: string;
  expected_roi?: number;
  actual_roi?: number;
  status: 'active' | 'completed' | 'cancelled' | 'paused';
  notes?: string;
  created_at: string;
  updated_at: string;
}
```

This comprehensive API documentation provides examples for all major functionality in the ChatSEO platform, supporting both agency and brand user workflows.