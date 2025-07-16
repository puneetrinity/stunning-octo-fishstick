# ChatSEO Platform

A comprehensive platform for monitoring brand mentions across AI platforms (ChatGPT, Claude, Gemini) with advanced citation analysis, competitor tracking, and content recommendations.

## 🚀 Features

### **For Agencies** 🏢
- **Multi-Client Management**: Manage multiple clients from a single dashboard
- **ROI Tracking**: Track expensive review site investments (G2, Capterra, etc.)
- **White-Label Reporting**: Generate branded reports for clients
- **Performance Metrics**: Monitor mentions, AI citations, traffic value
- **Client Onboarding**: Streamlined client setup and brand assignment

### **For Brands** 🏷️
- **Brand Monitoring**: Track mentions across AI platforms
- **Competitive Intelligence**: Compare performance against competitors
- **Content Recommendations**: AI-powered content optimization suggestions
- **Sentiment Analysis**: Understand how your brand is perceived
- **Citation Analysis**: Track prominence and context of mentions

### **Common Features** ⚡
- **Multi-Platform Support**: OpenAI, Anthropic, Google, and more
- **Advanced Analytics**: Detailed insights and exportable reports
- **Real-time Notifications**: Instant alerts for significant changes
- **Flexible Pricing**: Plans for every business size and type

## 🏗️ Architecture

Built with modern, scalable architecture:

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15 + Redis
- **Queue**: Celery with Redis broker
- **Authentication**: JWT-based security
- **Deployment**: Docker + Kubernetes ready
- **Monitoring**: Prometheus + Grafana

## 🛠️ Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if running locally)
- Redis 7+ (if running locally)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chat-seo-platform
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Access the application**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Flower (Celery monitoring): http://localhost:5555

### Manual Setup (Without Docker)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up databases**
   ```bash
   # PostgreSQL
   createdb chatseo_dev
   createdb chatseo_test
   
   # Redis (start service)
   redis-server
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the application**
   ```bash
   uvicorn main:app --reload
   ```

## 📊 API Documentation

### Authentication
- `POST /api/v1/auth/register` - User registration (supports dual user types)
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Get user profile
- `PUT /api/v1/auth/me` - Update profile
- `POST /api/v1/auth/change-password` - Change password

### Brands (All Users)
- `GET /api/v1/brands` - List user brands
- `POST /api/v1/brands` - Create brand
- `PUT /api/v1/brands/{id}` - Update brand
- `DELETE /api/v1/brands/{id}` - Delete brand
- `GET /api/v1/brands/{id}/stats` - Get brand statistics
- `POST /api/v1/brands/bulk` - Bulk create brands

### Clients (Agency Users Only)
- `GET /api/v1/clients` - List agency clients
- `POST /api/v1/clients` - Create new client
- `GET /api/v1/clients/{id}` - Get client details
- `PUT /api/v1/clients/{id}` - Update client
- `DELETE /api/v1/clients/{id}` - Delete client
- `GET /api/v1/clients/{id}/stats` - Get client statistics
- `POST /api/v1/clients/{id}/brands` - Assign brand to client
- `GET /api/v1/clients/{id}/dashboard` - Client dashboard data

### ROI Tracking (Agency Users Only)
- `GET /api/v1/roi/investments` - List ROI investments
- `POST /api/v1/roi/investments` - Create new investment
- `GET /api/v1/roi/investments/{id}` - Get investment details
- `PUT /api/v1/roi/investments/{id}` - Update investment
- `POST /api/v1/roi/investments/{id}/metrics` - Add performance metric
- `GET /api/v1/roi/investments/{id}/calculate` - Calculate ROI
- `GET /api/v1/roi/dashboard` - ROI dashboard data

### Pricing (All Users)
- `GET /api/v1/pricing` - Get all pricing plans
- `GET /api/v1/pricing/plan/{type}` - Get specific plan info
- `GET /api/v1/pricing/my-plan` - Get current user's plan
- `POST /api/v1/pricing/change-plan` - Change user's plan
- `GET /api/v1/pricing/compare` - Compare two plans

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chatseo_dev
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24

# AI APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Application
DEBUG=True
ENVIRONMENT=development
```

### Dual Pricing Strategy

**Brand Plans** (Direct Customers):
- **Brand Starter**: $199/month - 5 brands, 1,000 queries
- **Brand Professional**: $399/month - 15 brands, 3,000 queries

**Agency Plans** (Agency Customers):
- **Agency Starter**: $299/month - 5 clients, ROI tracking
- **Agency Pro**: $599/month - 15 clients, white-label reports
- **Agency Enterprise**: $1,299/month - Unlimited clients, custom features

## 🧪 Testing

Run tests with pytest:

```bash
# Unit tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_auth.py
```

## 📈 Development Roadmap

### Phase 1: MVP (Months 1-2) ✅
- [x] Basic authentication system
- [x] Database schema and migrations
- [x] Docker containerization
- [ ] AI platform integrations
- [ ] Basic monitoring engine
- [ ] Simple dashboard

### Phase 2: Market Validation (Months 3-4)
- [ ] Enhanced monitoring features
- [ ] Competitive analysis
- [ ] Email notifications
- [ ] Payment integration
- [ ] Beta testing program

### Phase 3: Advanced Features (Months 5-6)
- [ ] Content recommendations
- [ ] Agency dashboard
- [ ] Advanced analytics
- [ ] API access
- [ ] White-label reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Email: support@chatseo.com
- Documentation: [docs.chatseo.com](https://docs.chatseo.com)
- Issues: [GitHub Issues](https://github.com/your-repo/issues)

## 🏆 Acknowledgments

- FastAPI for the excellent framework
- SQLAlchemy for database ORM
- Redis for caching and queuing
- All AI platform providers for their APIs