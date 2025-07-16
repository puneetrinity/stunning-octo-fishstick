# ChatSEO Platform 🚀

A comprehensive platform for monitoring brand mentions across AI platforms (ChatGPT, Claude, Gemini) with advanced NLP citation analysis, Reddit intelligence tracking, and ROI-focused review site monitoring.

## 🎯 **Market-Validated MVP Complete**

Built on **Reddit intelligence** from real B2B practitioners, this platform addresses the exact pain point: *"we don't know exactly how much we are being mentioned and why"* while focusing on the **6% of ChatGPT sources from Reddit** and **expensive but effective review sites**.

## 🚀 **Core Features**

### **🤖 Multi-AI Platform Monitoring**
- **ChatGPT (OpenAI)**: Primary AI platform with advanced citation extraction
- **Claude (Anthropic)**: Conversational AI with growing user base
- **Gemini (Google)**: Google's AI platform with structured analysis
- **Cross-Platform Analytics**: Combined insights and recommendations

### **📊 Advanced NLP Citation Extraction**
- **spaCy + Transformers Pipeline**: State-of-the-art entity recognition
- **Sentiment Analysis**: Contextual sentiment with confidence scoring
- **Prominence Scoring**: Position-based importance analysis
- **Contextual Analysis**: Recommendation, comparison, and question contexts
- **Citation Quality**: Comprehensive quality assessment metrics

### **🔍 Reddit Intelligence Tracking**
- **6% of ChatGPT Sources**: Critical Reddit monitoring based on market research
- **Industry-Specific Subreddits**: Targeted monitoring by business category
- **Sentiment Analysis**: Reddit-specific sentiment patterns
- **Authority Correlation**: Track Reddit influence on ChatGPT responses

### **💰 Review Site ROI Tracking**
- **Major Platforms**: G2, Capterra, TrustRadius, Gartner monitoring
- **Investment Analysis**: Track $2K-15K monthly review site spend
- **ROI Calculation**: Measure expensive review site effectiveness
- **Authority Scoring**: Weight by platform authority and AI citation frequency

### **📈 Real-Time Monitoring Dashboard**
- **Live Progress Tracking**: Real-time monitoring session updates
- **Combined Analytics**: Cross-platform performance insights
- **Smart Recommendations**: AI-powered optimization suggestions
- **Professional UI**: Next.js 14 with TypeScript and Tailwind CSS

## 🏗️ **Architecture**

### **Backend Stack**
- **FastAPI**: High-performance Python web framework
- **PostgreSQL 15**: Primary database with advanced indexing
- **Redis**: Caching and task queue management
- **Celery**: Background task processing
- **Docker**: Containerized deployment

### **Frontend Stack**
- **Next.js 14**: Modern React framework with App Router
- **TypeScript**: Full type safety throughout
- **Tailwind CSS**: Professional design system
- **Recharts**: Interactive data visualizations
- **JWT Authentication**: Secure user management

### **AI & NLP Stack**
- **OpenAI API**: ChatGPT integration
- **Anthropic API**: Claude integration
- **Google Gemini API**: Gemini integration
- **spaCy**: Advanced NLP processing
- **Transformers**: Hugging Face models for sentiment/NER
- **Sentence Transformers**: Semantic similarity analysis

## 🛠️ **Quick Start**

### **Prerequisites**
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- PostgreSQL 15+ and Redis 7+ (if running locally)

### **Development Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/puneetrinity/stunning-octo-fishstick.git
   cd chat-seo-platform
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

5. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Access the application**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Flower (Celery monitoring)**: http://localhost:5555

### **Manual Setup (Without Docker)**

1. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Set up databases
   createdb chatseo_dev
   redis-server
   
   # Run migrations
   alembic upgrade head
   
   # Start the backend
   uvicorn main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📊 **API Documentation**

### **Authentication**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user profile

### **Brand Management**
- `GET /api/v1/brands` - List user brands
- `POST /api/v1/brands` - Create brand
- `PUT /api/v1/brands/{id}` - Update brand
- `DELETE /api/v1/brands/{id}` - Delete brand

### **Monitoring**
- `POST /api/v1/monitor/start` - Start monitoring session
- `GET /api/v1/monitor/status/{session_id}` - Get monitoring status
- `GET /api/v1/monitor/results/{session_id}` - Get monitoring results
- `GET /api/v1/monitor/history` - Get monitoring history

### **Analytics**
- `GET /api/v1/analytics/dashboard` - Dashboard statistics
- `GET /api/v1/analytics/competitor-analysis` - Competitor analysis
- `GET /api/v1/analytics/sentiment-trends` - Sentiment trends
- `GET /api/v1/analytics/platform-performance` - Platform performance

### **Citations**
- `GET /api/v1/citations` - List citations with filtering
- `GET /api/v1/citations/{id}` - Get citation details
- `GET /api/v1/citations/export` - Export citations (CSV/JSON/PDF)

### **Review Sites**
- `GET /api/v1/review-sites/mentions` - List review site mentions
- `GET /api/v1/review-sites/roi/{brand}` - Get ROI metrics
- `GET /api/v1/review-sites/summary/{brand}` - Get review site summary

### **Reddit**
- `GET /api/v1/reddit/mentions` - List Reddit mentions
- `GET /api/v1/reddit/analytics/{brand}` - Get Reddit analytics

### **Advanced NLP**
- `GET /api/v1/nlp/insights/{brand}` - Get NLP citation insights
- `POST /api/v1/nlp/analyze` - Analyze text for entities
- `POST /api/v1/nlp/similarity` - Calculate semantic similarity

## 🔧 **Configuration**

### **Environment Variables**

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chatseo_dev
REDIS_URL=redis://localhost:6379/0

# JWT Security
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24

# AI Platform APIs
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Reddit API (optional)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret

# Application
DEBUG=True
ENVIRONMENT=development
```

### **Pricing Strategy (Reddit-Validated)**

**Brand Plans** (Direct B2B Companies):
- **Brand Starter**: $299/month - 5 brands, 1,000 queries, basic monitoring
- **Brand Professional**: $499/month - 15 brands, 3,000 queries, advanced analytics

**Agency Plans** (B2B Tech Agencies):
- **Agency Starter**: $399/month - 5 clients, ROI tracking, review site monitoring
- **Agency Pro**: $799/month - 15 clients, white-label reports, advanced ROI modeling
- **Agency Enterprise**: $1,599/month - Unlimited clients, custom integrations, dedicated support

## 🧪 **Testing**

```bash
# Backend tests
pytest
pytest --cov=app

# Frontend tests  
cd frontend
npm test
npm run test:coverage

# Integration tests
pytest tests/integration/

# Load testing
locust -f tests/load_test.py
```

## 📈 **Development Roadmap**

### **Phase 1: MVP (Months 1-2) ✅ COMPLETED**
- [x] **Multi-AI Platform Integration**: ChatGPT, Claude, Gemini
- [x] **Advanced NLP Citation Extraction**: spaCy + Transformers pipeline
- [x] **Reddit Monitoring**: 6% of ChatGPT sources tracking
- [x] **Review Site ROI Tracking**: G2, Capterra, TrustRadius, Gartner
- [x] **Production React Frontend**: Next.js 14 with TypeScript
- [x] **Real-time Monitoring**: Live progress tracking
- [x] **Database Schema**: Complete with migrations and indexing
- [x] **Authentication System**: JWT-based security
- [x] **Docker Deployment**: Production-ready containerization

### **Phase 2: Market Validation (Months 3-4)**
- [ ] **Beta Testing Program**: 50 target users from Reddit research
- [ ] **Payment Integration**: Stripe subscription management
- [ ] **Email Notifications**: Alert system for mentions
- [ ] **Advanced Analytics**: Competitive intelligence dashboard
- [ ] **API Rate Limiting**: Production-grade rate limiting
- [ ] **Performance Optimization**: Caching and query optimization

### **Phase 3: Scale & Growth (Months 5-6)**
- [ ] **White-Label Reporting**: Agency-branded reports
- [ ] **API Access**: Public API for enterprise clients
- [ ] **Mobile App**: React Native mobile application
- [ ] **Advanced Content Recommendations**: AI-powered content suggestions
- [ ] **Webhook Integrations**: Slack, Teams, custom webhooks
- [ ] **Multi-Language Support**: International market expansion

## 🎯 **Business Intelligence (Reddit-Validated)**

### **Key Market Insights**
- **Pain Point**: "We don't know exactly how much we are being mentioned and why"
- **Market Size**: ~5,000 B2B tech agencies globally
- **Spending Pattern**: $2K-10K/month on review sites (expensive but effective)
- **Reddit Importance**: 6% of ChatGPT sources are Reddit
- **Competitive Advantage**: No horizontal solution exists (Azoma is ecommerce-focused)

### **Validated Tactics (From Reddit Research)**
1. **Review Site Listings**: Expensive but effective for AI citations
2. **Reddit Community Building**: 6% of ChatGPT sources
3. **Authority Source Mentions**: "Totally unconnected authoritative sources"
4. **Detailed Comparison Content**: FAQ-style comparison posts
5. **Cross-Platform Monitoring**: Track mentions across all AI platforms

## 🚀 **Deployment**

### **Production Deployment**

```bash
# Build and deploy backend
docker build -t chatseo-backend .
docker run -p 8000:8000 chatseo-backend

# Build and deploy frontend
cd frontend
npm run build
npm start
```

### **Kubernetes Deployment**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatseo-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatseo-api
  template:
    metadata:
      labels:
        app: chatseo-api
    spec:
      containers:
      - name: api
        image: chatseo/api:latest
        ports:
        - containerPort: 8000
```

## 🔒 **Security Features**

- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API rate limiting and abuse prevention
- **HTTPS Enforcement**: SSL/TLS encryption
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Proper cross-origin resource sharing
- **Security Headers**: Comprehensive security headers

## 📊 **Monitoring & Analytics**

- **Prometheus Metrics**: Application performance monitoring
- **Grafana Dashboards**: Real-time monitoring dashboards
- **Structured Logging**: Comprehensive logging with structlog
- **Error Tracking**: Integrated error reporting
- **Performance Monitoring**: Query performance and optimization
- **User Analytics**: Usage patterns and feature adoption

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Development Guidelines**

- **Code Style**: Follow PEP 8 for Python, ESLint for TypeScript
- **Testing**: Maintain test coverage above 80%
- **Documentation**: Update docs for new features
- **Type Safety**: Use TypeScript for frontend, type hints for Python
- **Security**: Follow security best practices

## 📝 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

For support and questions:
- **Email**: support@chatseo.com
- **Documentation**: [docs.chatseo.com](https://docs.chatseo.com)
- **Issues**: [GitHub Issues](https://github.com/puneetrinity/stunning-octo-fishstick/issues)
- **Discord**: [ChatSEO Community](https://discord.gg/chatseo)

## 🏆 **Acknowledgments**

- **FastAPI**: Excellent Python web framework
- **Next.js**: React framework for production
- **spaCy**: Advanced NLP processing
- **Transformers**: Hugging Face model ecosystem
- **Reddit Community**: Market intelligence and validation
- **AI Platform Providers**: OpenAI, Anthropic, Google for their APIs

## 📈 **Success Metrics**

### **Technical Metrics**
- **Uptime**: 99.9% availability
- **Response Time**: <200ms average API response
- **Test Coverage**: >80% code coverage
- **Security**: Zero critical vulnerabilities

### **Business Metrics**
- **Customer Acquisition**: 50 beta users by Month 3
- **Monthly Recurring Revenue**: $15K by Month 4
- **Customer Retention**: <10% monthly churn
- **Market Validation**: Product-market fit indicators

---

**Built with ❤️ by the ChatSEO Team**

*Ready for beta testing and MVP launch! 🚀*