# Aksio Backend - Claude Agent Instructions

## 🚨 IMPORTANT: Start Here
**Before beginning any work, ALWAYS:**
1. **Read `README.md`** for project overview and setup instructions
2. **Check app-specific documentation** in `apps/{app_name}/README.md`
3. **Review recent test results** to understand current state
4. **Update documentation** when making any changes

## Project Overview
The Aksio backend is an educational platform combining AI-powered learning tools with Django REST Framework. While the infrastructure is deployed on Google Cloud Platform, many features are still in development.

## Current Status (As of July 2025)

### ✅ **COMPLETED FEATURES**
- **Infrastructure**: GCP deployment on Cloud Run with PostgreSQL
- **CI/CD Pipeline**: GitHub Actions with automated testing
- **User Authentication**: Custom User model with JWT authentication
- **Basic App Structure**: All Django apps created with health endpoints

### ⚠️ **PARTIALLY IMPLEMENTED**
- **Accounts App**: Authentication works but has test failures:
  - Email normalization issues (not converting to lowercase consistently)
  - Model methods returning empty strings instead of email fallbacks
  - Authentication returning 403 instead of 401 for unauthenticated requests
  
### ❌ **NOT IMPLEMENTED** (Template Only)
- **Courses App**: Only health check endpoint exists
- **Documents App**: Only health check endpoint exists
- **Assessments App**: Only health check endpoint exists
- **Chat App**: Only health check endpoint exists
- **Billing App**: Only health check endpoint exists
- **Learning App**: Only health check endpoint exists

## Test Status Summary
```
FAILED Tests: 16 failures
- accounts.tests.test_models: 4 failures
- accounts.tests.test_serializers: 2 failures
- accounts.tests.test_views: 2 failures
- accounts.tests.test_integration: 2 failures
- All other apps: Missing URL pattern errors (6 failures)
```

## Architecture Reality Check

### **What Actually Exists**
```
apps/
├── accounts/          # ✅ Implemented (with bugs)
│   ├── models.py     # Custom User model (email normalization issues)
│   ├── views.py      # Auth endpoints (403/401 status code issues)
│   ├── serializers.py # Login validation message issues
│   └── tests/        # Comprehensive tests (16 failures)
├── courses/          # ❌ Template only
├── documents/        # ❌ Template only
├── assessments/      # ❌ Template only
├── chat/            # ❌ Template only
├── billing/         # ❌ Template only
├── learning/        # ❌ Template only
└── core/            # ✅ Basic utilities implemented
```

### **Deployment Status**
- **Production**: Infrastructure deployed but app not fully functional
- **Database**: Cloud SQL configured but minimal data models
- **Storage**: GCS buckets created but not integrated
- **Secrets**: Configured in Secret Manager

## Immediate Fixes Needed

### 1. **Fix Accounts App** (CRITICAL)
```python
# Issues to fix in models.py:
- Email should be normalized to lowercase in save() and UserManager
- full_name property should return email when names are empty
- get_short_name() should return email when first_name is empty

# Issues to fix in serializers.py:
- Login serializer should return specific error messages
- Email should be normalized before authentication

# Issues to fix in settings:
- Add missing URL patterns for all apps
- Configure REST_FRAMEWORK properly for 401 responses
```

### 2. **Add Missing URL Patterns**
```python
# In aksio/urls.py, add:
path("api/v1/assessments/", include("assessments.urls")),
path("api/v1/billing/", include("billing.urls")),
path("api/v1/chat/", include("chat.urls")),
path("api/v1/courses/", include("courses.urls")),
path("api/v1/documents/", include("documents.urls")),
path("api/v1/learning/", include("learning.urls")),
```

## Development Workflow for Claude

### **Before Making Any Changes**
1. **Check Current State**
   ```bash
   # Run tests to see what's broken
   make test
   
   # Check specific app status
   make test-accounts
   ```

2. **Read Existing Documentation**
   - Main README.md
   - App-specific README in `apps/{app_name}/README.md`
   - Check for any docs/ folder content

3. **Understand the ACTUAL Implementation**
   - Don't assume features exist based on documentation
   - Check actual code files, not just README claims
   - Verify model implementations exist before using them

### **When Making Changes**
1. **Fix Existing Issues First**
   - Run tests to identify failures
   - Fix failing tests before adding features
   - Ensure accounts app works before building on it

2. **Update Documentation**
   - Update app README.md files
   - Keep this CLAUDE.md file current
   - Document actual implementation status

3. **Follow Test-Driven Development**
   ```bash
   # 1. Run existing tests
   make test-{app_name}
   
   # 2. Fix failures
   # 3. Add new tests for new features
   # 4. Implement features
   # 5. Update documentation
   ```

### **Code Quality Requirements**
```bash
# Always run before committing:
./scripts/format-code.sh

# Or manually:
black apps/
isort apps/
flake8 apps/
```

## Real Implementation Status by App

### **Accounts App** (Partially Working)
- ✅ Custom User model (UUID primary key, email auth)
- ✅ UserProfile model
- ✅ Registration/Login endpoints
- ✅ JWT authentication
- ❌ Email normalization bugs
- ❌ Model method bugs
- ❌ Authentication status code issues

### **All Other Apps** (Not Implemented)
Each app currently has only:
- Basic `apps.py` configuration
- Empty `models.py` with TODO comment
- Empty `serializers.py` with TODO comment
- Health check view returning `implemented: False`
- Basic URL pattern for health check
- One test file checking health endpoint

## Documentation Maintenance

### **When to Update Documentation**
1. **After fixing bugs** - Update status in CLAUDE.md
2. **After implementing features** - Update app README.md
3. **After adding models** - Document in app README.md
4. **After adding endpoints** - Update API documentation

### **Documentation Files to Maintain**
- `/README.md` - Overall project documentation
- `/CLAUDE.md` - This file, current implementation status
- `/apps/{app_name}/README.md` - App-specific documentation
- `/docs/` - Additional documentation as needed

## Common Pitfalls to Avoid

1. **Don't assume features exist** - Most apps are empty templates
2. **Don't trust outdated documentation** - Check actual code
3. **Don't skip tests** - They reveal the true state
4. **Don't implement new features on broken foundations** - Fix accounts first

## Current Priority Order

1. **Fix all accounts app test failures**
2. **Add missing URL patterns**
3. **Implement courses app models and basic CRUD**
4. **Implement document upload functionality**
5. **Then proceed with other apps**

## Useful Commands

```bash
# Check what's actually implemented
find apps -name "models.py" -exec grep -l "class.*Model" {} \;

# See current test failures
make test 2>&1 | grep -E "(FAILED|ERROR)"

# Check which apps have real implementations
for app in accounts courses documents assessments chat billing learning; do
  echo "=== $app ==="
  grep -c "TODO" apps/$app/models.py 2>/dev/null || echo "0"
done
```

## Remember

The Aksio backend is a **work in progress**. While the infrastructure is deployed and the accounts app has basic functionality, most features described in documentation are aspirational, not implemented. Always verify actual implementation before building on top of assumed functionality.

**Your first task should always be: Run the tests and fix what's broken.**