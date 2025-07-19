# Billing App Documentation

## Overview

The `billing` app handles subscription management, payment processing, and usage tracking for the Aksio platform. It provides comprehensive billing functionality with Stripe integration and flexible subscription plans.

## 🎯 Purpose

- **Subscription Management**: Handle user subscription plans and billing
- **Payment Processing**: Secure payment handling via Stripe
- **Usage Tracking**: Monitor feature usage and billing metrics
- **Invoice Management**: Generate and manage billing invoices
- **Plan Management**: Flexible subscription plan configuration

## 📋 Implementation Status

⚠️ **PARTIALLY IMPLEMENTED** - Basic models exist, full implementation needed

### ✅ Implemented
- Basic model structure
- Read-only API endpoints
- Basic subscription tracking

### ❌ Not Yet Implemented
- Stripe payment integration
- Subscription creation/cancellation
- Payment processing workflows
- Invoice generation
- Usage-based billing
- Webhook handling
- Advanced analytics

## 🏗️ Models

### Core Models

#### `SubscriptionPlan`
- **Purpose**: Define available subscription tiers
- **Key Fields**:
  - `name`: Plan name (e.g., "Basic", "Pro", "Enterprise")
  - `description`: Plan feature description
  - `price_monthly`: Monthly price in cents
  - `price_yearly`: Yearly price in cents (with discount)
  - `stripe_price_id_monthly`: Stripe price ID for monthly billing
  - `stripe_price_id_yearly`: Stripe price ID for yearly billing
  - `features`: Plan features (JSONField)
  - `limits`: Usage limits (JSONField)
  - `is_active`: Whether plan is available for signup
  - `trial_days`: Free trial period length
  - `created_at`: Plan creation date

#### `Subscription`
- **Purpose**: User subscription instances
- **Key Fields**:
  - `user`: Subscription owner (ForeignKey)
  - `plan`: Associated subscription plan (ForeignKey)
  - `stripe_subscription_id`: Stripe subscription identifier
  - `status`: active/trialing/past_due/canceled/unpaid
  - `current_period_start`: Current billing period start
  - `current_period_end`: Current billing period end
  - `trial_end`: Trial period end date
  - `cancel_at_period_end`: Whether to cancel at period end
  - `canceled_at`: Cancellation timestamp
  - `created_at`: Subscription creation date
  - `updated_at`: Last modification date

#### `Payment`
- **Purpose**: Track individual payment transactions
- **Key Fields**:
  - `user`: Payment user (ForeignKey)
  - `subscription`: Associated subscription (ForeignKey)
  - `stripe_payment_intent_id`: Stripe payment identifier
  - `amount`: Payment amount in cents
  - `currency`: Payment currency (default: USD)
  - `status`: succeeded/pending/failed/canceled
  - `payment_method`: card/bank_transfer/other
  - `failure_code`: Stripe failure code if failed
  - `failure_message`: Human-readable failure reason
  - `paid_at`: Payment completion timestamp
  - `created_at`: Payment attempt timestamp

#### `Invoice`
- **Purpose**: Billing invoices for subscriptions
- **Key Fields**:
  - `user`: Invoice recipient (ForeignKey)
  - `subscription`: Associated subscription (ForeignKey)
  - `stripe_invoice_id`: Stripe invoice identifier
  - `invoice_number`: Human-readable invoice number
  - `status`: draft/open/paid/void/uncollectible
  - `subtotal`: Invoice subtotal in cents
  - `tax_amount`: Tax amount in cents
  - `total`: Total amount in cents
  - `currency`: Invoice currency
  - `invoice_pdf_url`: PDF download URL
  - `due_date`: Payment due date
  - `paid_at`: Payment completion timestamp
  - `created_at`: Invoice generation timestamp

#### `UsageRecord`
- **Purpose**: Track feature usage for billing
- **Key Fields**:
  - `user`: Usage user (ForeignKey)
  - `subscription`: Associated subscription (ForeignKey)
  - `feature_type`: ai_responses/document_uploads/storage_gb/chat_messages
  - `usage_amount`: Quantity used
  - `billing_period_start`: Billing period start
  - `billing_period_end`: Billing period end
  - `recorded_at`: Usage recording timestamp
  - `metadata`: Additional usage data (JSONField)

#### `BillingAddress`
- **Purpose**: User billing information
- **Key Fields**:
  - `user`: Address owner (ForeignKey)
  - `line1`: Address line 1
  - `line2`: Address line 2 (optional)
  - `city`: City
  - `state`: State/province
  - `postal_code`: ZIP/postal code
  - `country`: Country code
  - `is_default`: Whether this is the default address

## 🛠️ API Endpoints

### Current Endpoints (Read-Only)

```
GET /api/v1/billing/plans/
    - List available subscription plans
    - Include features and pricing

GET /api/v1/billing/subscription/
    - Get user's current subscription
    - Include plan details and status

GET /api/v1/billing/payments/
    - List user's payment history
    - Include payment status and amounts

GET /api/v1/billing/invoices/
    - List user's invoices
    - Include download links
```

### Planned Endpoints (Not Implemented)

```
POST /api/v1/billing/subscribe/
    - Create new subscription
    - Initialize Stripe subscription

POST /api/v1/billing/cancel/
    - Cancel subscription
    - Handle cancellation timing

PUT /api/v1/billing/subscription/
    - Update subscription plan
    - Handle plan upgrades/downgrades

POST /api/v1/billing/payment-methods/
    - Add/update payment methods
    - Manage saved payment methods

GET /api/v1/billing/usage/
    - Get current usage statistics
    - Compare against plan limits

POST /api/v1/billing/preview-invoice/
    - Preview invoice for plan changes
    - Calculate prorations

POST /api/v1/billing/apply-coupon/
    - Apply discount coupon
    - Validate coupon codes

GET /api/v1/billing/download-invoice/{id}/
    - Download invoice PDF
    - Secure download with authentication
```

## 🔧 Services (Not Implemented)

### `StripeService`
- **Purpose**: Handle Stripe API integration
- **Methods** (Planned):
  - `create_customer()`: Create Stripe customer
  - `create_subscription()`: Start new subscription
  - `update_subscription()`: Modify existing subscription
  - `cancel_subscription()`: Cancel subscription
  - `process_payment()`: Handle payment processing
  - `handle_webhook()`: Process Stripe webhooks

### `SubscriptionManager`
- **Purpose**: Manage subscription lifecycle
- **Methods** (Planned):
  - `subscribe_user()`: Create user subscription
  - `upgrade_plan()`: Handle plan upgrades
  - `downgrade_plan()`: Handle plan downgrades
  - `cancel_subscription()`: Process cancellation
  - `reactivate_subscription()`: Resume canceled subscription

### `UsageTracker`
- **Purpose**: Track and bill for feature usage
- **Methods** (Planned):
  - `record_usage()`: Log feature usage
  - `check_limits()`: Verify usage against limits
  - `calculate_overage()`: Compute overage charges
  - `generate_usage_report()`: Create usage summaries

### `InvoiceGenerator`
- **Purpose**: Generate and manage invoices
- **Methods** (Planned):
  - `generate_invoice()`: Create billing invoice
  - `send_invoice()`: Email invoice to customer
  - `process_payment()`: Handle invoice payment
  - `handle_failed_payment()`: Manage payment failures

## 💳 Stripe Integration (Not Implemented)

### Webhook Handling
- **subscription.created**: New subscription setup
- **subscription.updated**: Subscription changes
- **subscription.deleted**: Subscription cancellation
- **invoice.payment_succeeded**: Successful payment
- **invoice.payment_failed**: Failed payment
- **customer.subscription.trial_will_end**: Trial expiration

### Payment Processing
- **Card Payments**: Credit/debit card processing
- **Payment Methods**: Saved payment method management
- **3D Secure**: Enhanced security for cards
- **Payment Intents**: Secure payment processing
- **Setup Intents**: Save payment methods

### Subscription Management
- **Plan Changes**: Upgrade/downgrade handling
- **Prorations**: Calculate partial billing periods
- **Trial Periods**: Manage free trial periods
- **Cancellations**: Handle subscription cancellations

## 📊 Usage Tracking (Not Implemented)

### Billable Features
- **AI Responses**: Count AI-generated responses
- **Document Uploads**: Track file uploads and processing
- **Storage Usage**: Monitor storage consumption
- **Chat Messages**: Count AI chat interactions
- **Assessment Generation**: Track AI-generated content

### Usage Limits
- **Plan-Based Limits**: Different limits per subscription tier
- **Overage Billing**: Charge for usage beyond limits
- **Soft Limits**: Warnings before hard limits
- **Usage Alerts**: Notify users approaching limits

### Analytics
- **Usage Trends**: Analyze usage patterns over time
- **Cost Optimization**: Identify cost-saving opportunities
- **Revenue Analytics**: Track revenue and churn
- **Feature Adoption**: Monitor feature usage rates

## 🔒 Security Considerations

### Payment Security
- **PCI Compliance**: Secure payment data handling
- **Stripe Elements**: Secure payment form integration
- **Webhook Verification**: Validate Stripe webhook signatures
- **Encryption**: Encrypt sensitive billing data

### Access Control
- **User Isolation**: Users can only access their billing data
- **Admin Access**: Controlled admin billing management
- **Audit Logging**: Track billing-related actions
- **Data Protection**: GDPR/privacy compliance

## 🧪 Testing (Minimal)

### Current Tests
- Basic model validation
- API endpoint accessibility
- Data serialization

### Needed Tests
- Stripe integration testing
- Payment flow testing
- Webhook handling testing
- Usage tracking testing
- Invoice generation testing

## 🔄 Integration Points

### External Dependencies
- **Stripe API**: Payment processing and subscription management
- **Email Service**: Invoice and notification delivery
- **Analytics Platform**: Usage and revenue analytics
- **Accounting System**: Financial reporting integration

### Internal Integrations
- **Accounts App**: User billing profile management
- **Usage Tracking**: Monitor feature usage across apps
- **Admin Interface**: Billing management dashboard
- **Notification System**: Billing alerts and reminders

## 📈 Business Models

### Subscription Tiers (Planned)
- **Free Tier**: Limited features with usage caps
- **Basic Plan**: Essential features for individual users
- **Pro Plan**: Advanced features for power users
- **Enterprise Plan**: Full features with high limits

### Pricing Strategy
- **Monthly/Yearly Options**: Discount for annual billing
- **Usage-Based Add-ons**: Pay for additional usage
- **Education Discounts**: Special pricing for students
- **Enterprise Pricing**: Custom pricing for large customers

## 🚀 Implementation Roadmap

### Phase 1: Core Billing
1. **Stripe Integration**: Set up Stripe API connection
2. **Subscription Creation**: Implement subscription signup
3. **Payment Processing**: Handle card payments
4. **Basic Webhooks**: Process essential Stripe events

### Phase 2: Advanced Features
1. **Plan Management**: Upgrade/downgrade functionality
2. **Usage Tracking**: Implement feature usage monitoring
3. **Invoice System**: Generate and manage invoices
4. **Payment Recovery**: Handle failed payments

### Phase 3: Analytics and Optimization
1. **Usage Analytics**: Detailed usage reporting
2. **Revenue Analytics**: Financial insights and reporting
3. **Churn Prevention**: Identify and prevent cancellations
4. **Optimization Tools**: Cost and usage optimization

## 📝 Configuration Requirements

### Stripe Setup
```python
# Environment variables needed
STRIPE_PUBLISHABLE_KEY = "pk_test_..."
STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."
STRIPE_API_VERSION = "2023-10-16"
```

### Subscription Plans Configuration
```python
SUBSCRIPTION_PLANS = {
    'free': {
        'ai_responses_limit': 50,
        'document_uploads_limit': 5,
        'storage_limit_gb': 1,
    },
    'basic': {
        'ai_responses_limit': 500,
        'document_uploads_limit': 50,
        'storage_limit_gb': 10,
    },
    # ... more plans
}
```

## 🐛 Known Issues

### Current Limitations
- **No Payment Processing**: Only read-only operations
- **No Stripe Integration**: Stripe connection not implemented
- **No Usage Tracking**: Feature usage not monitored
- **No Invoice Generation**: Cannot create invoices
- **Limited Testing**: Minimal test coverage

### Required Implementation
- Complete Stripe API integration
- Implement subscription lifecycle management
- Add comprehensive usage tracking
- Build invoice generation system
- Create webhook handling system
- Add extensive testing coverage

## 📋 Implementation Priority

### High Priority
1. **Stripe Integration**: Core payment processing
2. **Subscription Management**: Plan creation/cancellation
3. **Webhook Handling**: Process Stripe events
4. **Usage Tracking**: Monitor feature usage

### Medium Priority
1. **Invoice System**: Generate and manage invoices
2. **Payment Recovery**: Handle failed payments
3. **Plan Upgrades**: Seamless plan changes
4. **Usage Analytics**: Detailed usage insights

### Low Priority
1. **Advanced Analytics**: Revenue and churn analysis
2. **Optimization Tools**: Cost optimization features
3. **Enterprise Features**: Custom pricing and contracts
4. **International Support**: Multiple currencies and taxes