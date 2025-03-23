# Desktop Application MVP Requirements

## 1. Product Overview
- Windows desktop application
- Monthly subscription-based licensing model
- Target audience: Small user base (handful of users initially)

## 2. Core Features

### 2.1 Desktop Application
- Windows-only support
- Flask backend for AI logic running locally
- React frontend UI
- Websocket connection between backend and frontend
- UI improvements and bug fixes:
  - Resolve existing UI issues and inconsistencies
  - Implement minimal visual enhancements (improved logos and icons)
- Session management:
  - Archive and access to all previous chat sessions
  - Review-only mode for past conversations
  - Export functionality to download sessions as PDF files
- Core tool functionality:
  - COM SAP integration
  - File operation capabilities
  - BASH command execution
  - Computer action automation

### 2.2 Licensing System
- Monthly subscription ($X/month)
- X-week free trial period
- Online license verification required at each app launch
- Device-level binding (one machine per license)
- License key approach (vs. direct user login)

### 2.3 Observability
- Usage logging (app sessions, feature usage, errors)
- Server-side log storage in database
- [Optional] Basic analytics dashboard for monitoring
- [Important] Privacy-compliant data collection (Otherwise, strong consent required from customer that we are logging)

### 2.4 Web Portal
- Minimal web interface for subscription management
- User account creation and management:
  - Email registration with verification
  - Password creation with security requirements
  - Basic account profile (name, email, billing info)
- Payment processing integration
- License key generation and management
- User dashboard to view:
  - Subscription status
  - Billing history
  - Active devices
  - License key information

### 2.5 Scope Limitations
- Agent training self-service portal is excluded from MVP
- Creation of new workflows is excluded from MVP
- Attachment of existing workflows is tentatively excluded (to be confirmed)
- Advanced UI redesign deferred to post-MVP release
- Only minimal visual enhancements included in initial release

## 3. User Flow

### 3.1 Initial Download & Trial
1. User visits marketing page and clicks "Download Now"
2. User downloads and installs Windows application
3. On first launch, app initiates trial mode:
   - User is prompted to provide email address to start trial
   - App calls server to register device and email for trial
   - Server creates a basic user account and records a Trial License Key for the device
   - User receives welcome email with:
     - Trial information (expiration date, features)
     - Download link to the application executable
     - Link to web portal for account management
   - User can use the app for X days with daily server checks

### 3.2 Subscription Purchase
1. When trial expires, user is prompted to purchase subscription
2. User navigates to web portal via link in app or email
3. If account is incomplete, user completes registration:
   - Sets password
   - Adds required profile information
   - Provides billing details
4. User completes payment process (via Stripe/PayPal)
5. System generates license key with subscription status
6. User receives license key (displayed on portal or via email)

### 3.3 License Activation
1. User enters license key in desktop application
2. App validates key with server (including device ID)
3. Server binds license to device if not already bound elsewhere
4. App stores license key locally in encrypted format

### 3.4 Ongoing Usage
1. Each time app launches, it verifies license validity with server
2. If subscription is active, app functions normally
3. If subscription expired/canceled, user is prompted to renew

## 4. Technical Components

### 4.1 Backend Server (Minimal)
- Simple Flask server hosted on VPS or cloud service
- Database for storing:
  - License keys
  - Subscription status
  - Trial expiry dates
  - Billing dates
  - Device IDs

### 4.2 Server API Endpoints
- `/api/create_subscription`: Generate license after payment
- `/api/validate_license`: Verify license validity and bind device
- `/api/start_trial`: Register new device for trial period

### 4.3 Desktop Application
- Local storage for license key
- Device ID generation for binding
- License validation on startup
- Trial mode functionality
- License key entry interface

### 4.4 Payment Processing
- Integration with Stripe/PayPal for subscription payments
- Webhook handling for subscription status updates

## 5. Implementation Priorities

### Phase 1: Core Application
- Develop basic desktop application with Flask backend and React UI
- Implement local functionality without licensing

### Phase 2: Licensing Infrastructure
- Set up minimal backend server
- Implement database schema for licenses
- Create API endpoints for license validation

### Phase 3: Web Portal & Payment
- Develop simple web portal for subscriptions
- Integrate payment processing
- Implement license key generation

### Phase 4: Desktop Integration
- Add license validation to desktop app
- Implement trial mode
- Add license key entry interface

### Phase 5: Testing & Deployment
- Test end-to-end subscription flow
- Verify device binding functionality
- Deploy MVP to production

## 6. Future Considerations (Post-MVP)
- Refund handling
- License transfer between devices
- Automatic updates
- Usage analytics
- Additional platform support
