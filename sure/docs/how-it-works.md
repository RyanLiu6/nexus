# How Sure Works

## Overview

Sure is an open-source, self-hosted personal finance application that helps you track, analyze, and optimize your financial life. It's a community-maintained fork of the archived Maybe Finance project, offering a complete financial management solution that you control.

**Key Philosophy:**
- **Privacy First**: Self-hosted means your financial data never leaves your infrastructure
- **Open Source**: Full transparency with AGPLv3 license
- **All-in-One**: Accounts, budgets, transactions, insights, and AI assistance in one platform

## Architecture

Sure uses a modern Ruby on Rails stack with the following components:

### Core Services

1. **Web Application (Rails)**
   - Main application server handling HTTP requests
   - User interface and API endpoints
   - Runs on port 3000 by default

2. **Background Worker (Sidekiq)**
   - Processes asynchronous jobs (account syncing, transaction categorization)
   - Handles scheduled tasks (daily balance updates, recurring transaction creation)
   - Uses Redis for job queue management

3. **PostgreSQL Database**
   - Stores all financial data (accounts, transactions, budgets)
   - User information and preferences
   - AI conversation history

4. **Redis Cache**
   - Job queue for Sidekiq
   - Session storage
   - Application caching

### Data Flow

```
User Browser
    ↓
Web Application (Rails)
    ↓
├── Direct DB queries → PostgreSQL
├── Background jobs → Redis → Sidekiq Worker → PostgreSQL
├── AI requests → OpenAI/Ollama → PostgreSQL (for context)
└── Account syncing → External APIs → Sidekiq → PostgreSQL
```

## Core Features

### 1. Account Management

**Supported Account Types:**
- **Depository**: Checking, savings, money market accounts
- **Credit**: Credit cards, lines of credit
- **Investment**: Brokerage accounts, retirement accounts (401k, IRA)
- **Loan**: Mortgages, auto loans, student loans
- **Property**: Real estate, vehicles
- **Crypto**: Bitcoin, Ethereum, other cryptocurrencies
- **Other Assets**: Art, collectibles, business interests

**Connection Methods:**
- **Automatic Syncing**: Connect to 10,000+ financial institutions via Plaid integration
- **Manual Entry**: Add accounts manually and update balances as needed
- **CSV Import**: Import transaction history from bank exports

### 2. Transaction Management

**Transaction Types:**
- **Income**: Paychecks, bonuses, investment returns, etc.
- **Expense**: Bills, purchases, fees, etc.
- **Transfer**: Money movement between your accounts

**Transaction Metadata:**
- Date and amount
- Merchant and category
- Custom notes
- Tags for flexible organization
- Account linkage
- Transfer matching

**Bulk Operations:**
- Import from CSV
- Bulk categorization via rules
- Batch editing
- Search and filter

### 3. Budgeting System

**Budget Types:**
- **Category Budgets**: Set spending limits per category (e.g., $500/month for groceries)
- **Smart Allocations**: Automatically distribute income across categories
- **Rollover Budgets**: Unused budget carries to next period

**Budget Features:**
- Monthly or custom period budgets
- Visual progress bars showing spending vs. budget
- Alerts when approaching or exceeding limits
- Historical budget vs. actual comparison

### 4. Categories & Merchants

**Category System:**
- Pre-defined category hierarchy (Food & Dining → Restaurants, Groceries)
- Subcategories for granular tracking
- Custom categories as needed
- Category-based insights and reports

**Merchant Management:**
- Automatic merchant detection from transaction data
- Manual merchant assignment
- Merchant aliases (e.g., "AMZN*" → "Amazon")
- LLM-enhanced merchant recognition

### 5. Rules Engine

**What Are Rules?**
Rules are automated conditions that perform actions on your transactions, saving time and ensuring consistency.

**Rule Conditions:**
- Transaction name/description contains text
- Amount equals, less than, or greater than
- Category is/isn't
- Merchant is/isn't
- Account is/isn't
- Date range
- Transaction notes

**Rule Actions:**
- Set category
- Set merchant
- Add/update notes
- Add tags
- Exclude from reports/budgets

**Rule Features:**
- Import/Export rules for backup or sharing
- View recent rule executions
- Pre-fill suggestions based on existing transactions
- Apply rules retroactively or only to new transactions

### 6. Reporting & Insights

**Available Reports:**
- **Net Worth Tracking**: Historical view of assets minus liabilities
- **Income vs. Expenses**: Monthly/yearly trends
- **Cash Flow Analysis**: Money in vs. money out
- **Category Breakdown**: Spending by category with charts
- **Account Performance**: Growth over time for investments
- **Budget Reports**: Actual vs. budgeted spending

**Visualization:**
- Line charts for trends over time
- Pie charts for category distribution
- Bar charts for comparative analysis
- Customizable date ranges

### 7. AI Assistant

**Capabilities:**
- Natural language queries about your finances
- Spending pattern analysis
- Budget recommendations
- Financial forecasting
- Anomaly detection

**Example Queries:**
- "How much did I spend on restaurants last month?"
- "What are my top 5 expense categories this year?"
- "Am I on track to meet my savings goal?"
- "Show me unusual transactions in the last week"

## Data Model

### Key Entities

**Account**
- Type (depository, credit, investment, etc.)
- Institution name
- Current balance
- Historical balances (tracked daily)
- Account number (encrypted)
- Currency

**Transaction**
- Date, amount, name
- Account (from/to)
- Category, merchant
- Notes, tags
- Marked as transfer, pending, excluded
- Enrichment data (provider merchant, category suggestions)

**Category**
- Name, color, icon
- Parent category (for hierarchy)
- User-defined or system default

**Budget**
- Category
- Amount limit
- Period (monthly, yearly, custom)
- Rollover settings

**Rule**
- Name, enabled status
- Conditions (JSON-based)
- Actions (JSON-based)
- Priority order

## Security & Privacy

### Data Protection

**Encryption:**
- Passwords hashed with bcrypt
- Sensitive account data encrypted at rest
- HTTPS enforced for all connections (via Traefik in this setup)

**Authentication:**
- Email/password authentication
- Session-based login
- Password reset via email
- (Optional) OAuth support for Google, GitHub

**Access Control:**
- Multi-user support with isolated data
- No cross-user data access
- API authentication via tokens

### Self-Hosting Benefits

**Privacy:**
- Your data never leaves your infrastructure
- No third-party analytics or tracking
- Full control over backups and retention

**Security:**
- You control the security perimeter
- No dependency on external service availability
- Audit the code yourself (open source)

## Workflow Examples

### Daily Use
1. Check dashboard for net worth and recent transactions
2. Review uncategorized transactions and assign categories
3. Chat with AI assistant for quick insights
4. Check budget progress

### Weekly Review
1. Review all transactions for the week
2. Apply any needed corrections (wrong categories, missing merchants)
3. Check budget status and adjust spending if needed
4. Review upcoming bills and transfers

### Monthly Analysis
1. Run monthly spending report
2. Compare actual vs. budgeted spending
3. Analyze trends (up/down from last month)
4. Update budgets for next month based on actuals
5. Export transactions for tax prep or external analysis

### Setup & Onboarding
1. Create account and log in
2. Connect bank accounts (via Plaid) or add manually
3. Import historical transactions (CSV or sync)
4. Set up categories and merchants
5. Create budgets for key categories
6. Create rules for recurring transactions
7. (Optional) Configure AI assistant

## Performance Considerations

### Scalability

**Database:**
- Transactions are the highest volume table
- Indexed on account_id, date, category_id, merchant_id for fast queries
- Partitioning possible for very large datasets (1M+ transactions)

**Background Jobs:**
- Account syncing can be slow (depends on bank API)
- Daily balance calculations run overnight
- AI categorization batched for efficiency

**Caching:**
- Dashboard data cached for fast page loads
- Account balances cached with TTL
- Reports cached per date range

### Resource Usage

**Typical Resource Needs:**
- **CPU**: Low to medium (spikes during sync or AI requests)
- **Memory**: 512MB-1GB for web/worker combined
- **Storage**: Depends on transaction volume (typically 100MB-1GB database)
- **Network**: Minimal (only external API calls for syncing)

## Extensibility

### API Access

Sure includes a REST API for programmatic access:
- `/api/accounts` - List accounts
- `/api/transactions` - CRUD operations on transactions
- `/api/categories` - Manage categories
- `/api/budgets` - Budget management

**Use Cases:**
- Custom mobile apps
- Integration with other tools (spreadsheets, analytics)
- Automated transaction import from proprietary sources

### Customization

**Theme & Branding:**
- Custom CSS for colors and fonts
- Logo replacement
- White-label deployment

**Feature Extensions:**
- Add custom transaction types
- Implement custom rules engine logic
- Integrate with additional APIs (crypto prices, stock quotes)

## Comparison to Other Tools

| Feature | Sure (Self-Hosted) | YNAB | Mint | Actual Budget |
|---------|-------------------|------|------|---------------|
| **Cost** | Free (hosting only) | $99/year | Free (ads) | $3-5/month |
| **Privacy** | Full control | Cloud service | Cloud + ads | Self-hosted |
| **Open Source** | Yes (AGPLv3) | No | No | Yes (MIT) |
| **AI Assistant** | Yes (configurable) | No | No | No |
| **Bank Sync** | Yes (Plaid) | Yes | Yes | No |
| **Mobile App** | Web-based | iOS/Android | iOS/Android | Web-based |
| **Multi-Currency** | Yes | Limited | No | Yes |

**When to Choose Sure:**
- You value privacy and want self-hosted
- You want AI-powered insights
- You're comfortable with Docker/self-hosting
- You want to customize or extend the platform
- You prefer open source solutions

**When to Choose Alternatives:**
- You want native mobile apps (YNAB)
- You want zero-setup cloud solution (Mint, YNAB)
- You don't need AI features (Actual Budget)

## References

- [Sure Official Website](https://sure.am/)
- [Sure GitHub Repository](https://github.com/we-promise/sure)
- [Original Maybe Finance](https://github.com/maybe-finance/maybe)
- [Plaid Documentation](https://plaid.com/docs/)
- [Rails Documentation](https://guides.rubyonrails.org/)
