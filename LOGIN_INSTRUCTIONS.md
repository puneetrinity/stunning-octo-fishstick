# 🔐 ChatSEO Platform - Login Instructions

## 🎯 **Two Ways to Access Your Platform**

### **Option 1: Development Interface (Working Now!)**
- **URL**: https://stunning-octo-fishstick-production.up.railway.app/
- **Status**: ✅ **Fully functional**
- **Features**: Complete authentication system, monitoring interface

### **Option 2: React Frontend (Deploying)**
- **URL**: https://frontend-production-ce4b.up.railway.app
- **Status**: 🔄 **Redeploying** (should be ready in ~5 minutes)
- **Features**: Professional dashboard, charts, brand management

## 🔑 **How to Create Your Login**

### **Method 1: Use the Development Interface**
1. **Visit**: https://stunning-octo-fishstick-production.up.railway.app/
2. **Scroll to "User Authentication" section**
3. **Fill in registration form**:
   - **Email**: your-email@company.com
   - **Password**: Min 8 chars with uppercase, lowercase, number
4. **Click "Register"**
5. **Use same credentials to login**

### **Method 2: API Registration (Advanced)**
```bash
# Run the test user creation script
./create-test-user.sh
```

### **Method 3: Manual API Call**
```bash
curl -X POST "https://stunning-octo-fishstick-production.up.railway.app/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@company.com",
    "password": "YourPassword123",
    "full_name": "Your Name",
    "company_name": "Your Company",
    "user_type": "brand"
  }'
```

## 📋 **Registration Requirements**

### **Required Fields:**
- **Email**: Valid email address
- **Password**: 
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter  
  - At least 1 number
- **User Type**: Choose "brand" or "agency"

### **Optional Fields:**
- **Full Name**: Your display name
- **Company Name**: Your company
- **Plan Type**: Auto-assigned based on user type

## 🏢 **User Types & Plans**

### **Brand Users**
- **brand_starter**: $299/month - 5 brands, 1000 queries
- **brand_professional**: $499/month - 15 brands, 3000 queries

### **Agency Users**  
- **agency_starter**: $399/month - 5 clients
- **agency_pro**: $799/month - 15 clients
- **agency_enterprise**: $1599/month - Unlimited clients

## 🎯 **Quick Test Account**

**Want to test immediately?** Use the development interface:

1. **Visit**: https://stunning-octo-fishstick-production.up.railway.app/
2. **Register with**:
   - Email: test@yourcompany.com
   - Password: TestPass123
   - User Type: brand
3. **Start monitoring immediately!**

## 🚀 **After Registration**

### **What You Can Do:**
1. **Add Brands**: Monitor your company and competitors
2. **Start Monitoring**: Track mentions across AI platforms
3. **View Analytics**: See charts and sentiment analysis
4. **Export Data**: Download reports in multiple formats

### **Supported Platforms:**
- ✅ **ChatGPT**: Primary AI platform monitoring
- ✅ **Claude**: Anthropic AI platform
- ✅ **Gemini**: Google AI platform
- ✅ **Reddit**: 6% of ChatGPT sources
- ✅ **Review Sites**: G2, Capterra, TrustRadius, Gartner

## 🔧 **Troubleshooting**

### **If Registration Fails:**
1. Check password requirements
2. Ensure email format is valid
3. Try the development interface instead
4. Check database connection in /ready endpoint

### **If Login Fails:**
1. Verify credentials are correct
2. Check account was created successfully
3. Try password reset (if implemented)
4. Contact support

## 💡 **Pro Tips**

### **Getting Started:**
1. **Register as "brand" user** for easiest setup
2. **Use development interface** until React frontend is ready
3. **Add 2-3 brand names** to start monitoring
4. **Include competitors** for comparison analysis

### **Best Practices:**
- Use strong, unique password
- Add multiple brand variations (e.g., "OpenAI", "Open AI")
- Monitor both brand and competitor mentions
- Check results regularly for new insights

Your ChatSEO Platform is ready to start tracking your brand mentions across AI platforms! 🎉