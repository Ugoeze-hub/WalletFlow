# WalletFlow - Wallet Service API

A comprehensive backend wallet service with Paystack integration, JWT authentication, and API key management system. This service allows users to deposit money, manage wallet balances, view transaction history, and transfer funds between users.

---

## Features

### Core Features
- **Google OAuth Authentication** - Secure user login via Google (browser-based due to CORS)
- **JWT Token Management** - Stateless authentication with token expiration
- **API Key System** - Service-to-service authentication with permissions
- **Wallet Management** - Create and manage user wallets
- **Paystack Integration** - Process deposits via Nigeria's leading payment gateway
- **Transaction History** - Track all wallet transactions
- **Fund Transfers** - Send money between user wallets
- **Webhook Handling** - Real-time payment notifications from Paystack

### Security Features
- Dual authentication (JWT + API Keys)
- API key permissions system (read, deposit, transfer)
- Maximum 5 active API keys per user
- API key expiration and rollover
- Paystack webhook signature verification
- Password hashing for API keys

---

## 🛠️ Tech Stack

| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Backend framework |
| **PostgreSQL** | Database with SQLAlchemy ORM |
| **JWT** | Token-based authentication |
| **Google OAuth** | User authentication |
| **Paystack API** | Payment processing |
| **bcrypt** | Password hashing |
| **httpx** | Async HTTP client |
| **Pydantic** | Data validation |

---

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Paystack account (for payment processing)
- Google Cloud Console account (for OAuth)

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/wallet_db

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# JWT
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Paystack
PAYSTACK_SECRET_KEY=sk_test_your_paystack_secret
PAYSTACK_PUBLIC_KEY=pk_test_your_paystack_public
PAYSTACK_WEBHOOK_SECRET=whsec_your_webhook_secret
PAYSTACK_INITIALIZE_URL=https://api.paystack.co/transaction/initialize
PAYSTACK_VERIFY_URL=https://api.paystack.co/transaction/verify

# API Keys
API_KEY_PREFIX=sk_test_
MAX_API_KEYS_PER_USER=5

# App
APP_ENV=development
```

---

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd WalletFlow
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL database
```sql
CREATE DATABASE wallet_db;
CREATE USER wallet_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE wallet_db TO wallet_user;
```

### 5. Run database setup
```bash
# The app will automatically create tables on startup
python -m app.main
```

### 6. Run the application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 API Documentation

Once running, access the interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔌 API Endpoints

### Authentication Endpoints

#### 1. Google OAuth Login
```http
GET /auth/google
```

**Description**: Redirects to Google login page.

> **Note**: OAuth works in the browser due to FastAPI CORS configuration. The task specification did not require returning specific data from this endpoint.

---

#### 2. Google OAuth Callback
```http
GET /auth/google/callback
```

**Description**: Receives Google authentication code and returns JWT token.

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJ...",
  "token_type": "bearer"
}
```

---

### API Key Management

#### 3. Create API Key
```http
POST /keys/create
```

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Request Body**:
```json
{
  "name": "wallet-service",
  "permissions": ["deposit", "transfer", "read"],
  "expiry": "1D"
}
```

**Expiry Options**: `1H`, `1D`, `1M`, `1Y`

**Response**:
```json
{
  "api_key": "sk_test_abc123xyz...",
  "expires_at": "2025-01-01T12:00:00Z"
}
```

---

#### 4. Rollover Expired API Key
```http
POST /keys/rollover
```

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Request Body**:
```json
{
  "expired_key_id": "FGH2485K6KK79GKG9GKGK",
  "expiry": "1M"
}
```

---

### Wallet Operations

#### 5. Initialize Deposit
```http
POST /wallet/deposit
```

**Authentication**: JWT or API Key with `deposit` permission

**Headers**:
```
Authorization: Bearer <jwt_token>
OR
x-api-key: <api_key>
```

**Request Body**:
```json
{
  "amount": 5000
}
```

**Response**:
```json
{
  "reference": "dep_abc123xyz",
  "authorization_url": "https://paystack.com/checkout/...",
  "message": "Deposit of 5000 successful"
}
```

---

#### 6. Check Deposit Status
```http
GET /wallet/deposit/{reference}/status
```

**Authentication**: JWT or API Key with `read` permission

**Response**:
```json
{
  "reference": "dep_abc123xyz",
  "status": "pending|success|failed",
  "amount": 5000
}
```

---

#### 7. Get Wallet Balance
```http
GET /wallet/balance
```

**Authentication**: JWT or API Key with `read` permission

**Response**:
```json
{
  "wallet_number": "4566678954356",
  "balance": 15000
}
```

---

#### 8. Transfer Funds
```http
POST /wallet/transfer
```

**Authentication**: JWT or API Key with `transfer` permission

**Request Body**:
```json
{
  "wallet_number": "4566678954356",
  "amount": 3000
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Transfer completed"
}
```

---

#### 9. Get Transaction History
```http
GET /wallet/transactions
```

**Authentication**: JWT or API Key with `read` permission

**Response**:
```json
[
  {
    "type": "deposit",
    "amount": 5000,
    "status": "success",
    "reference": "dep_abc123",
    "created_at": "2025-12-10T21:04:44.425Z",
    "description": null
  }
]
```

---

### Paystack Webhook

#### 10. Paystack Webhook Endpoint
```http
POST /wallet/paystack/webhook
```

**Description**: Receives payment notifications from Paystack. Configure this URL in your Paystack dashboard.

**Note**: This endpoint is called automatically by Paystack. No manual authentication required.

---

## Authentication Methods

### Method 1: JWT Token (User Authentication)
```http
Authorization: Bearer <jwt_token>
```

- Obtained from Google OAuth login
- Short-lived (30 minutes default)
- Grants all permissions

### Method 2: API Key (Service Authentication)
```http
x-api-key: <api_key>
```

- Created via `/keys/create` endpoint
- Long-lived (configurable expiry)
- Permission-based access
- Maximum 5 active keys per user

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Wallets Table
```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    wallet_number VARCHAR(20) UNIQUE NOT NULL,
    balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    wallet_id UUID REFERENCES wallets(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'NGN',
    transaction_type VARCHAR(20) NOT NULL, -- 'deposit', 'transfer', 'withdrawal'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'success', 'failed'
    recipient_wallet_id UUID REFERENCES wallets(id),
    sender_wallet_id UUID REFERENCES wallets(id),
    description TEXT,
    reference VARCHAR(255) UNIQUE NOT NULL,
    transaction_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id VARCHAR(50) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL, -- Hashed API key
    permissions JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);
```

---

## Project Structure
```
wallet_service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Database connection setup
│   ├── config.py            # Configuration settings
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── wallet.py
│   │   ├── transaction.py
│   │   └── api_key.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── wallet.py
│   │   └── api_key.py
│   ├── auth/                # Authentication logic
│   │   ├── __init__.py
│   │   ├── jwt_auth.py
│   │   ├── api_key_auth.py
│   │   └── google_oauth.py
│   ├── routes/              # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── wallet.py
│   │   └── api_keys.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── wallet_service.py
│   │   ├── transaction_service.py
│   │   └── paystack.py
│   └── utils/               # Helper functions
│       ├── __init__.py
│       └── security.py
├── requirements.txt
├── .env                    # Environment variables
└── README.md
```

---

## Payment Flow

### Deposit Flow

1. **User initiates deposit** via `/wallet/deposit`
2. **System calls Paystack** to initialize transaction
3. **User redirected** to Paystack payment page
4. **User completes payment** on Paystack
5. **Paystack sends webhook** to `/wallet/paystack/webhook`
6. **System processes webhook**:
   - Verifies signature
   - Updates transaction status
   - Credits user wallet
7. **User can check status** via `/wallet/deposit/{reference}/status`

### Transfer Flow

1. **User initiates transfer** via `/wallet/transfer`
2. **System validates**:
   - Sufficient balance
   - Valid recipient wallet
   - Not transferring to self
3. **System processes transfer**:
   - Deducts from sender wallet
   - Credits recipient wallet
   - Creates transaction records for both parties
4. **Both parties can view** in `/wallet/transactions`

---

## Security Best Practices

1. **Environment Variables**: Never commit `.env` file to version control
2. **API Keys**: Store hashed, never plain text
3. **Webhook Verification**: Always verify Paystack signatures
4. **CORS Configuration**: Configure properly for production
5. **Rate Limiting**: Implement rate limiting for production
6. **Database Backups**: Regular backups of transaction data
7. **Logging**: Log all financial transactions for audit trails

---

## Testing

### Test Deposit Flow
```bash
# 1. Login and get JWT token
curl http://localhost:8000/auth/google

# 2. Initialize deposit
curl -X POST http://localhost:8000/wallet/deposit \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000}'

# 3. Complete payment on Paystack checkout page

# 4. Check deposit status
curl http://localhost:8000/wallet/deposit/dep_xyz123/status \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Test with API Key
```bash
# 1. Create API key
curl -X POST http://localhost:8000/keys/create \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-key",
    "permissions": ["read", "deposit"],
    "expiry": "1D"
  }'

# 2. Use API key for requests
curl http://localhost:8000/wallet/balance \
  -H "x-api-key: <your_api_key>"
```

---

## ⚠️ Important Notes

### Google OAuth
- OAuth authentication works **in the browser only** due to FastAPI CORS configuration
- The task specification did not require specific return data from OAuth endpoints
- Users are redirected through Google's authentication flow


### Production Deployment
- Use HTTPS for all endpoints
- Configure proper CORS settings
- Set up database connection pooling
- Implement rate limiting
- Add request logging and monitoring

---

## Troubleshooting

### Webhook Not Receiving Events
1. Check Paystack Dashboard → Webhooks for delivery attempts
2. Verify webhook URL is publicly accessible (use ngrok for local)
3. Check webhook signature in logs
4. Ensure PAYSTACK_WEBHOOK_SECRET is correct

### OAuth Not Working
1. Verify Google OAuth credentials in `.env`
2. Check redirect URI matches Google Cloud Console
3. Ensure CORS is properly configured
4. Test in browser, not API client

### Database Connection Issues
1. Verify PostgreSQL is running
2. Check DATABASE_URL in `.env`
3. Ensure database user has proper permissions

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Paystack for payment processing
- FastAPI for the amazing framework
- Google OAuth for authentication
- HNG

---

## 📧 Support

For issues or questions, please open an issue on GitHub or contact [eluchieugoeze@gmail.com]