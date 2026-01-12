# AI Integration & Transaction Categorization

## Overview

Sure includes powerful AI capabilities powered by Large Language Models (LLMs) to automate transaction categorization, enhance merchant detection, and provide intelligent financial insights through a conversational assistant.

**Key AI Features:**
- **Automatic Transaction Categorization**: AI suggests categories for transactions
- **Merchant Enhancement**: Improves merchant name detection and normalization
- **Chat Assistant**: Natural language queries about your finances
- **Rules Suggestions**: AI recommends automation rules based on patterns

**AI Options:**
- **Cloud-based**: Use OpenAI, Google Gemini, Anthropic Claude, or other providers
- **Local LLMs**: Self-host with Ollama for complete privacy

## Quick Start

### Option 1: Cloud AI (OpenAI)

The simplest setup uses OpenAI's API:

1. **Get an API Key**: Visit [OpenAI Platform](https://platform.openai.com/api-keys)

2. **Set Environment Variable**: Add to your `.env` file:
   ```bash
   SURE_OPENAI_ACCESS_TOKEN=sk-proj-your-key-here
   ```

3. **Restart Sure**:
   ```bash
   docker compose restart sure-web sure-worker
   ```

4. **Enable in UI**:
   - Go to Settings → Self-Hosting → AI Provider
   - Agree to enable AI features

**That's it!** Sure will now use GPT-4.1 for all AI operations.

**Cost Estimate:**
- Typical usage: $5-20/month for personal finance tracking
- Chat message: ~$0.01-0.05 each
- Auto-categorization: ~$0.05-0.15 per 25 transactions

### Option 2: Local AI (Ollama)

For complete privacy and no ongoing costs:

1. **Install Ollama** (if not using Docker compose):
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull a Model**:
   ```bash
   # Recommended: balanced performance (requires 16GB VRAM)
   ollama pull llama3.1:13b

   # Budget: smaller model (requires 8GB VRAM)
   ollama pull gemma2:7b
   ```

3. **Configure Sure** in `.env`:
   ```bash
   SURE_OPENAI_ACCESS_TOKEN=ollama-local
   SURE_OPENAI_URI_BASE=http://localhost:11434/v1
   SURE_OPENAI_MODEL=llama3.1:13b
   ```

4. **Restart Sure**:
   ```bash
   docker compose restart sure-web sure-worker
   ```

**Note**: See [docker-compose-ollama.yml](../docker-compose-ollama.yml) for integrated Ollama setup.

**✨ Excellent option for Mac Mini M4 users!** Apple Silicon has great ML performance - see details below.

### Option 3: Anthropic Claude (API)

For excellent reasoning with financial data:

**⚠️ Important: Claude Pro vs Claude API**

- **Claude Pro** ($20/month): Web interface subscription - **does NOT provide API access**
- **Claude API**: Separate pay-per-use service with API keys - **what you need for Sure**

If you have Claude Pro, you still need to sign up separately for Claude API.

1. **Get an API Key**: Visit [Anthropic Console](https://console.anthropic.com/)
   - Sign up for API access (separate from Pro subscription)
   - Add payment method (pay-per-use pricing)
   - Create an API key

2. **Configure Sure** in `.env`:
   ```bash
   SURE_OPENAI_ACCESS_TOKEN=sk-ant-your-anthropic-key-here
   SURE_OPENAI_URI_BASE=https://api.anthropic.com/v1
   SURE_OPENAI_MODEL=claude-sonnet-4-20250514
   ```

3. **Restart Sure**:
   ```bash
   docker compose restart sure-web sure-worker
   ```

**Recommended Models:**
- `claude-sonnet-4-20250514` - Best balance (Sonnet 4.5)
- `claude-opus-4-20250514` - Highest quality (Opus 4.5)
- `claude-haiku-4-20250514` - Fastest, cheapest (Haiku 4.5)

**Cost Estimate:**
- Sonnet: ~$10-25/month for typical usage
- Haiku: ~$3-8/month (budget option)
- **Note**: This is in addition to your Pro subscription if you have one

**Pros:**
- Excellent reasoning for complex financial questions
- Strong function calling support
- Good at detecting spending patterns
- Privacy-focused company

**Note:** Claude requires OpenAI-compatible wrapper. If direct API doesn't work, use OpenRouter (see Option 5).

### Option 4: Google Gemini Pro (Direct API)

For fast, cost-effective AI:

1. **Get an API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)

2. **Install Gemini adapter** (if using direct API):
   ```bash
   # Note: Sure uses OpenAI-compatible API, so you'll need OpenRouter or a proxy
   # Direct Gemini API is not OpenAI-compatible
   # Recommended: Use Option 5 (OpenRouter) instead
   ```

**Alternative: Use OpenRouter** (recommended - see Option 5)

**Cost Estimate:**
- Gemini Pro: ~$3-10/month
- Gemini Flash: ~$1-5/month (fastest, cheapest)

### Option 5: Multiple Providers via OpenRouter (Recommended)

**Best choice for flexibility and cost optimization**

[OpenRouter](https://openrouter.ai/) provides a single API for multiple providers including Claude, Gemini, Deepseek, and many others.

1. **Get an API Key**: Visit [OpenRouter](https://openrouter.ai/) and create account

2. **Configure Sure** in `.env`:
   ```bash
   SURE_OPENAI_ACCESS_TOKEN=sk-or-v1-your-openrouter-key
   SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
   SURE_OPENAI_MODEL=<model-from-list-below>
   ```

3. **Choose a Model**:

   **For Chat Assistant (Financial Advisor):**
   ```bash
   # Anthropic Claude (Excellent reasoning)
   SURE_OPENAI_MODEL=anthropic/claude-sonnet-4.5

   # Google Gemini (Fast and affordable)
   SURE_OPENAI_MODEL=google/gemini-pro-1.5

   # Deepseek (Very affordable, good quality)
   SURE_OPENAI_MODEL=deepseek/deepseek-chat

   # OpenAI (Most reliable)
   SURE_OPENAI_MODEL=openai/gpt-4-turbo
   ```

   **For Transaction Categorization (Budget Option):**
   ```bash
   # Gemini Flash (Fastest, cheapest)
   SURE_OPENAI_MODEL=google/gemini-flash-1.5

   # Deepseek (Very affordable)
   SURE_OPENAI_MODEL=deepseek/deepseek-chat

   # Claude Haiku (Fast and good)
   SURE_OPENAI_MODEL=anthropic/claude-haiku-4.5
   ```

4. **Restart Sure**:
   ```bash
   docker compose restart sure-web sure-worker
   ```

**Benefits:**
- **Single API key** for all providers
- **Automatic fallback** if one provider is down
- **Cost tracking** and comparison
- **Easy switching** between models
- **No vendor lock-in**

**Cost Comparison (via OpenRouter):**

| Provider | Model | Cost/Month* | Best For |
|----------|-------|------------|----------|
| **Deepseek** | deepseek-chat | $2-5 | Budget-conscious, good quality |
| **Google** | gemini-flash-1.5 | $3-8 | Speed + low cost |
| **Google** | gemini-pro-1.5 | $5-12 | Balanced performance |
| **Anthropic** | claude-haiku-4.5 | $4-10 | Fast, good reasoning |
| **Anthropic** | claude-sonnet-4.5 | $10-25 | Best reasoning |
| **OpenAI** | gpt-4-turbo | $8-20 | Most reliable |

*Typical personal finance usage: 150 transactions/month, 20 chat queries/month

### Option 6: Deepseek (Direct API)

**Most affordable cloud option with good quality**

1. **Get an API Key**: Visit [Deepseek Platform](https://platform.deepseek.com/)

2. **Configure Sure** in `.env`:
   ```bash
   SURE_OPENAI_ACCESS_TOKEN=sk-deepseek-your-key-here
   SURE_OPENAI_URI_BASE=https://api.deepseek.com/v1
   SURE_OPENAI_MODEL=deepseek-chat
   ```

3. **Restart Sure**:
   ```bash
   docker compose restart sure-web sure-worker
   ```

**Pros:**
- **Extremely affordable**: ~70-90% cheaper than GPT-4
- **Good quality**: Competitive with GPT-4 for many tasks
- **OpenAI-compatible API**: Easy integration

**Cons:**
- Newer provider (less track record)
- Function calling support may vary
- Response times can be slower

**Cost Estimate:**
- ~$1-5/month for typical personal finance usage
- Great for transaction categorization
- Good enough for basic financial advice

## Privacy & Data Security: Who Gets Your Data?

### ⚠️ CRITICAL: Understanding Data Flow

**YES - When using cloud AI, the AI provider gets your financial data.**

Here's exactly what happens:

```
Your Transaction Data
        ↓
   Sure Application (your server)
        ↓
   [LEAVES YOUR INFRASTRUCTURE]
        ↓
   AI Provider (OpenAI/Anthropic/Google/Deepseek)
        ↓
   AI processes your data
        ↓
   Returns suggestion
        ↓
   Sure displays result
```

### What Data Do AI Providers See?

#### For Transaction Categorization:

The AI provider receives:
```json
{
  "transaction_name": "WHOLEFDS LAX 10488",
  "amount": -127.43,
  "date": "2024-01-15",
  "account_name": "Chase Checking",
  "your_categories": ["Groceries", "Food & Dining", "Shopping", ...],
  "notes": "Weekly grocery shopping"
}
```

**They see:**
- ✅ Where you shop (merchant names)
- ✅ How much you spend
- ✅ When you spend it
- ✅ What account you use
- ✅ Transaction notes you write

**They DON'T see:**
- ❌ Your password
- ❌ Account numbers or routing numbers
- ❌ Your name (usually)
- ❌ Full transaction history (only what you ask about)

#### For Chat Assistant (Financial Advisor):

When you ask: *"How much did I spend on restaurants last month?"*

The AI provider receives:
```json
{
  "question": "How much did I spend on restaurants last month?",
  "transactions": [
    {"name": "Chipotle", "amount": -12.50, "date": "2024-12-05", "category": "Dining"},
    {"name": "Olive Garden", "amount": -45.67, "date": "2024-12-10", "category": "Dining"},
    // ... all matching transactions
  ],
  "account_balances": {"Chase Checking": 2450.00},
  "budget_data": {"Dining Budget": 300, "Spent": 234}
}
```

**They see:**
- ✅ Your full question/query
- ✅ All relevant financial data to answer it
- ✅ Account balances
- ✅ Budget information
- ✅ Spending patterns
- ✅ Income information (if queried)
- ✅ Net worth (if queried)

### Provider Data Policies

#### OpenAI
- **Data Retention**: 30 days
- **Training**: API data NOT used for training (per policy)
- **Privacy Policy**: [OpenAI Privacy](https://openai.com/policies/privacy-policy)
- **Location**: US-based
- **Trust**: High (established, audited)

#### Anthropic (Claude)
- **Data Retention**: Zero retention for API calls (per policy)
- **Training**: Not used for training
- **Privacy Policy**: [Anthropic Privacy](https://www.anthropic.com/legal/privacy)
- **Location**: US-based
- **Trust**: Very High (privacy-focused company)
- **Note**: Anthropic explicitly markets privacy as a differentiator

#### Google (Gemini)
- **Data Retention**: Not used for training (per enterprise policy)
- **Privacy Policy**: [Google AI Privacy](https://ai.google/responsibility/privacy/)
- **Location**: Global infrastructure
- **Trust**: Medium-High (Google's broader data practices may concern some)

#### Deepseek
- **Data Retention**: Check their policy
- **Privacy Policy**: [Deepseek Privacy](https://platform.deepseek.com/)
- **Location**: China-based company
- **Trust**: Lower (newer, less transparency)
- **⚠️ Note**: Some users may have concerns about data jurisdiction

#### OpenRouter
- **Data Flow**: Acts as proxy - data still goes to underlying provider
- **Privacy Policy**: [OpenRouter Privacy](https://openrouter.ai/privacy)
- **Benefit**: Single point of integration, but doesn't change data exposure
- **Trust**: Medium (adds another party to data flow)

### Local AI (Ollama): Complete Privacy

When using Ollama:

```
Your Transaction Data
        ↓
   Sure Application (your server)
        ↓
   Ollama (your server)
        ↓
   LLM Model (running on your GPU)
        ↓
   [NEVER LEAVES YOUR INFRASTRUCTURE]
        ↓
   Returns suggestion
        ↓
   Sure displays result
```

**Privacy Benefits:**
- ✅ Zero external data sharing
- ✅ Complete control over data
- ✅ No API provider sees anything
- ✅ Works offline
- ✅ Complies with strictest privacy regulations

**Trade-offs:**
- ⚠️ Requires GPU hardware (16GB+ VRAM recommended)
- ⚠️ Setup complexity
- ⚠️ Ongoing maintenance
- ⚠️ Slightly lower quality than GPT-4/Claude

## Recommendations: What Should You Do?

### Decision Framework

Ask yourself these questions:

#### 1. How sensitive is your financial data?

**Low Sensitivity** (basic personal finance):
- No unusual income sources
- Standard bank accounts
- Nothing you'd be uncomfortable with tech companies seeing
- **→ Recommendation: Cloud AI (any provider)**

**Medium Sensitivity** (prefer privacy but not critical):
- Comfortable with reputable companies seeing data
- Want convenience of cloud
- Privacy matters but not a dealbreaker
- **→ Recommendation: Anthropic Claude or OpenAI**

**High Sensitivity** (strict privacy requirements):
- Business finances
- Regulated industry
- Multiple income sources
- Large amounts
- Privacy is non-negotiable
- **→ Recommendation: Local AI (Ollama)**

#### 2. What's your budget?

**Budget-Conscious** ($0-5/month):
- **→ Deepseek** (cloud, ~$2-5/month)
- **→ Ollama** (local, $0 API fees but hardware + electricity)

**Moderate** ($5-15/month):
- **→ Gemini Flash** (fast, affordable)
- **→ Claude Haiku** (good balance)
- **→ OpenAI GPT-4o-mini**

**Premium** ($15-30/month):
- **→ Claude Sonnet** (best reasoning)
- **→ OpenAI GPT-4** (most reliable)

#### 3. What's your technical comfort level?

**Beginner** (want simplest setup):
- **→ OpenAI** (most straightforward)
- **→ OpenRouter** (single API for multiple providers)

**Intermediate**:
- **→ Anthropic Claude**
- **→ Gemini via OpenRouter**
- **→ Deepseek**

**Advanced** (comfortable with self-hosting):
- **→ Ollama** (complete control)

#### 4. Do you have GPU hardware?

**No GPU** or **GPU <8GB VRAM**:
- **→ Cloud AI only** (local AI won't work well)

**8-16GB VRAM**:
- **→ Cloud AI recommended** (local AI possible but limited)
- Can run smaller Ollama models (7B-9B parameters)

**16GB+ VRAM**:
- **→ Local AI (Ollama) is viable**
- Can run good models (13B-32B parameters)
- Significant privacy benefits

**24GB+ VRAM**:
- **→ Local AI (Ollama) recommended** for privacy
- Excellent quality with large models

### Specific Recommendations by Use Case

#### Use Case 1: Basic Transaction Categorization Only

**Don't need chat assistant, just auto-categorization**

**Best Choice: Deepseek or Gemini Flash**
```bash
# Via OpenRouter
SURE_OPENAI_ACCESS_TOKEN=sk-or-your-key
SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
SURE_OPENAI_MODEL=deepseek/deepseek-chat
# OR
SURE_OPENAI_MODEL=google/gemini-flash-1.5
```

**Why:**
- Categorization is simpler than chat
- Don't need premium models
- Very affordable ($2-5/month)
- Good accuracy for this task

#### Use Case 2: Financial Advisor + Categorization

**Want AI chat for financial advice**

**Best Choice: Claude Sonnet or GPT-4**
```bash
# Anthropic Claude (Best reasoning)
SURE_OPENAI_ACCESS_TOKEN=sk-ant-your-key
SURE_OPENAI_URI_BASE=https://api.anthropic.com/v1
SURE_OPENAI_MODEL=claude-sonnet-4-20250514

# OR OpenAI (Most reliable)
SURE_OPENAI_ACCESS_TOKEN=sk-proj-your-key
# No URI needed for OpenAI
```

**Why:**
- Better at complex financial reasoning
- Superior function calling
- More accurate insights
- Worth the extra cost ($10-25/month)

#### Use Case 3: Maximum Privacy (Business/Regulated)

**Privacy is non-negotiable**

**Best Choice: Local AI (Ollama)**
```bash
SURE_OPENAI_ACCESS_TOKEN=ollama-local
SURE_OPENAI_URI_BASE=http://sure-ollama:11434/v1
SURE_OPENAI_MODEL=llama3.1:13b
```

**Why:**
- Zero data leaves your infrastructure
- Complete control
- Regulatory compliance
- No ongoing API costs

**Hardware Investment:**
- RTX 4070 Ti or better (~$800-1200)
- Or rent GPU server (~$50-100/month)

#### Use Case 4: Best Value (Balance of Cost/Quality)

**Want good quality without breaking the bank**

**Best Choice: OpenRouter with Model Selection**
```bash
SURE_OPENAI_ACCESS_TOKEN=sk-or-your-key
SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1

# For categorization (cheap):
SURE_OPENAI_MODEL=deepseek/deepseek-chat

# For chat (good quality):
SURE_OPENAI_MODEL=anthropic/claude-sonnet-4.5
```

**Why:**
- Single API key
- Choose best model per task
- Easy to switch
- Cost tracking built-in

### My Personal Recommendation

**For Most Users:**

**Start with OpenRouter + Claude Sonnet:**
```bash
SURE_OPENAI_ACCESS_TOKEN=sk-or-v1-your-openrouter-key
SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
SURE_OPENAI_MODEL=anthropic/claude-sonnet-4.5
```

**Why:**
1. **Anthropic** is the most privacy-conscious cloud provider
2. **Claude** has excellent financial reasoning
3. **OpenRouter** gives you flexibility to switch
4. **Cost** is reasonable ($10-20/month)
5. **Setup** is simple (5 minutes)

**Then Consider:**
- **Monitor costs** for 2-3 months
- **If costs exceed $30/month** → Consider local AI (Ollama)
- **If quality issues** → Switch to GPT-4 (via OpenRouter)
- **If want cheaper** → Switch to Deepseek or Gemini Flash

**For Privacy-Focused Users:**

**Go with Ollama if you have hardware:**
```bash
SURE_OPENAI_ACCESS_TOKEN=ollama-local
SURE_OPENAI_URI_BASE=http://sure-ollama:11434/v1
SURE_OPENAI_MODEL=qwen2.5:14b
```

**If no hardware:**
- **Anthropic Claude** (most privacy-focused cloud option)
- Accept that cloud AI = data sharing
- Review Anthropic's privacy policy

### Red Flags / What to Avoid

❌ **Avoid Deepseek if:**
- You have concerns about Chinese data jurisdiction
- Your financial data is highly sensitive
- You're in a regulated industry

❌ **Avoid Google Gemini if:**
- You're uncomfortable with Google's data practices
- You use Google services and want separation
- Privacy is a top concern

❌ **Avoid Local AI if:**
- You don't have adequate GPU (need 16GB+ VRAM)
- You're not comfortable with self-hosting
- You want the absolute best quality

❌ **Avoid OpenAI if:**
- Budget is very tight (there are cheaper options)
- You want the most privacy-focused cloud option (choose Anthropic)

## AI Features Deep Dive

### 1. Automatic Transaction Categorization

**What it does:**
Analyzes transaction details (merchant, amount, description) and suggests appropriate categories.

**How it works:**
1. New transaction created (from bank sync or manual entry)
2. Background job sends transaction data to LLM
3. LLM analyzes and suggests category + merchant
4. Suggestion displayed in UI for approval or auto-applied (if enabled)

**What the AI sees:**
```json
{
  "name": "WHOLEFDS LAX 10488",
  "amount": -127.43,
  "date": "2024-01-15",
  "account": "Chase Checking",
  "existing_categories": ["Groceries", "Food & Dining", "Health & Wellness", ...],
  "notes": ""
}
```

**AI Response:**
```json
{
  "category": "Groceries",
  "merchant": "Whole Foods",
  "confidence": "high"
}
```

**Configuration:**

Enable auto-categorization:
- Settings → Transactions → Auto-categorize transactions
- Choose: "Always", "Suggestions Only", or "Disabled"

**Best Practices:**
- **Review suggestions** before trusting fully (especially early on)
- **Provide feedback** by correcting wrong categories (AI learns from existing data)
- **Use notes** for ambiguous transactions (AI uses notes for context)
- **Create rules** for recurring transactions (faster and free)

**Example Use Cases:**
- Monthly paycheck → "Income: Salary"
- "AMZN*DIGITAL" → "Shopping: Online"
- "Chevron Gas" → "Transportation: Fuel"
- "Netflix.com" → "Entertainment: Streaming"

### 2. Merchant Enhancement

**What it does:**
Cleans up messy merchant names from bank data.

**Examples:**
- `WHOLEFDS LAX 10488` → `Whole Foods`
- `SQ *COFFEE SHOP` → `Coffee Shop`
- `AMZN MKTP US*AB123XYZ` → `Amazon`
- `TST* RESTAURANT NAME` → `Restaurant Name`

**How it works:**
1. Bank provides raw merchant name (often abbreviated/coded)
2. AI analyzes and suggests clean merchant name
3. Sure displays both "provider merchant" (raw) and "family merchant" (cleaned)
4. You can accept AI suggestion or set manually

**Configuration:**
- Settings → Transactions → Merchant Enhancement
- Enable "Auto-enhance merchants"

**Benefits:**
- Better transaction search (search for "Amazon" finds all Amazon transactions)
- Cleaner merchant reports
- Easier manual categorization

**LLM Prompt Example:**
```
Given the transaction name "WHOLEFDS LAX 10488", extract the actual merchant name.
Return only the merchant name, cleaned and normalized.
```

**AI Response:**
```
Whole Foods
```

### 3. AI Chat Assistant

**What it does:**
Answers questions about your finances using natural language.

**How it works:**
1. You ask a question in chat interface
2. AI analyzes your question
3. AI calls appropriate functions to fetch your data (accounts, transactions, etc.)
4. AI formulates response based on your actual financial data

**Available Functions:**
- `get_transactions(date_range, account, category, merchant)` - Fetch transactions
- `get_accounts()` - List accounts and balances
- `get_balance_sheet()` - Assets vs. liabilities
- `get_income_statement(date_range)` - Income vs. expenses
- `get_budget_progress(category)` - Budget status

**Example Conversation:**

**You:** "How much did I spend on groceries last month?"

**AI:** "Analyzing your data..." [calls `get_transactions`]

**AI:** "You spent $687.43 on groceries in December 2024 across 18 transactions. This is about 15% higher than your monthly average of $597."

**You:** "Which grocery store did I spend the most at?"

**AI:** [calls `get_transactions` filtered by category]

**AI:** "Your top grocery stores in December were:
1. Whole Foods: $342.18 (8 transactions)
2. Trader Joe's: $215.50 (6 transactions)
3. Safeway: $129.75 (4 transactions)"

**Advanced Queries:**

**Financial Health:**
```
"What's my current net worth and how has it changed this year?"
```

**Spending Patterns:**
```
"Do I spend more on weekends or weekdays?"
"What time of month do I typically overspend?"
```

**Budgeting:**
```
"Which budget categories am I on track for this month?"
"If I continue my current spending, will I stay within my monthly budget?"
```

**Comparisons:**
```
"Compare my spending this quarter to last quarter"
"Am I spending more or less than the same month last year?"
```

**Forecasting:**
```
"Based on my income and spending, how long until I reach $25,000 in savings?"
"What will my net worth be in 6 months if trends continue?"
```

**Anomaly Detection:**
```
"Show me any unusual transactions in the last two weeks"
"Are there any recurring charges I might have forgotten about?"
```

### 4. Rules Suggestions

**What it does:**
AI suggests automation rules based on existing transaction patterns.

**How it works:**
1. AI analyzes recent transactions you've manually categorized
2. Identifies patterns (e.g., all "NETFLIX" → "Entertainment")
3. Suggests creating a rule to automate this

**Example:**

After you've categorized 3+ Netflix transactions as "Entertainment: Streaming", AI suggests:

```
Suggested Rule: "Auto-categorize Netflix"

IF transaction name contains "NETFLIX"
THEN set category to "Entertainment: Streaming"
     set merchant to "Netflix"

Apply to: Future transactions only
```

**Benefits:**
- Faster transaction processing
- Consistent categorization
- Reduced manual work

## Cloud AI Providers

### OpenAI (Recommended)

**Pros:**
- Best function calling support
- Most reliable
- Excellent categorization accuracy
- Fast response times

**Cons:**
- Costs money per API call
- Data sent to OpenAI servers
- Requires internet connection

**Models:**
- **gpt-4.1** (default): Best balance of cost and quality
- **gpt-5**: Latest model, highest quality, more expensive
- **gpt-4o-mini**: Cheaper option, still good quality

**Setup:**
```bash
SURE_OPENAI_ACCESS_TOKEN=sk-proj-your-key-here
# That's it! Uses OpenAI by default
```

**Pricing** (as of Jan 2025):
- GPT-4.1: ~$5-15 per 1M input tokens, ~$15-60 per 1M output tokens
- GPT-5: ~2-3x more expensive
- GPT-4o-mini: ~$0.15 per 1M input tokens (very cheap)

**Cost Optimization:**
- Use GPT-4o-mini for categorization (bulk operations)
- Use GPT-4.1 for chat (better reasoning)
- Monitor usage via [OpenAI Usage Dashboard](https://platform.openai.com/usage)

### Google Gemini (via OpenRouter)

**Why OpenRouter?**
- Single API key for multiple providers
- Automatic failover
- Cost tracking
- Competitive pricing

**Setup:**
1. Get API key from [OpenRouter](https://openrouter.ai/)
2. Configure:
   ```bash
   SURE_OPENAI_ACCESS_TOKEN=sk-or-your-openrouter-key
   SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
   SURE_OPENAI_MODEL=google/gemini-2.5-flash
   ```

**Recommended Models:**
- `google/gemini-2.5-flash`: Fast and capable
- `google/gemini-2.5-pro`: Higher quality for complex queries

**Pros:**
- Often cheaper than OpenAI
- Fast response times
- Good multilingual support

**Cons:**
- Slightly less reliable function calling than GPT-4
- May require more prompt tuning

### Anthropic Claude (via OpenRouter)

**Setup:**
```bash
SURE_OPENAI_ACCESS_TOKEN=sk-or-your-openrouter-key
SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
SURE_OPENAI_MODEL=anthropic/claude-4.5-sonnet
```

**Models:**
- `anthropic/claude-4.5-sonnet`: Excellent reasoning, good with financial data
- `anthropic/claude-4.5-haiku`: Faster and cheaper

**Pros:**
- Superior reasoning for complex financial questions
- Strong privacy focus
- Excellent long-context handling

**Cons:**
- More expensive than GPT-4
- Function calling support varies by model

### Other Providers

**Groq** (Fast inference):
```bash
SURE_OPENAI_URI_BASE=https://api.groq.com/openai/v1
SURE_OPENAI_ACCESS_TOKEN=your-groq-key
SURE_OPENAI_MODEL=llama3-70b-8192
```

**Together AI** (Open models):
```bash
SURE_OPENAI_URI_BASE=https://api.together.xyz/v1
SURE_OPENAI_ACCESS_TOKEN=your-together-key
SURE_OPENAI_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

## Local AI with Ollama

### Why Local AI?

**Privacy:**
- Your financial data never leaves your server
- No third-party access
- Ideal for sensitive information

**Cost:**
- No per-request fees
- Only hardware and electricity costs
- Can be cheaper at scale

**Offline:**
- Works without internet
- No dependency on external services
- Consistent availability

**Control:**
- Choose your own models
- Update on your schedule
- Full customization

### Hardware Requirements

#### NVIDIA/AMD GPUs (Linux/Windows)

**Minimum (8GB VRAM):**
- Models: `llama3.2:7b`, `gemma2:7b`, `qwen2.5:7b`
- Performance: Basic chat, slower categorization
- GPUs: RTX 3070, RTX 4060 Ti, AMD RX 6700 XT

**Recommended (16GB VRAM):**
- Models: `llama3.1:13b`, `qwen2.5:14b`
- Performance: Good chat and categorization
- GPUs: RTX 4070 Ti, RTX 3090, AMD RX 7900 XT

**Ideal (24GB+ VRAM):**
- Models: `qwen2.5:32b`, `llama3.1:70b` (with quantization)
- Performance: Excellent quality
- GPUs: RTX 4090, RTX 6000 Ada

#### Apple Silicon (Mac M1/M2/M3/M4)

**✨ Great news for Mac Mini M4 users!** Apple Silicon has excellent ML performance using unified memory.

**Mac Mini M4 Base (16GB RAM):**
- Models: `llama3.2:3b`, `qwen2.5:7b`, `gemma2:9b`
- Performance: Good for basic chat and categorization
- **Recommended model**: `qwen2.5:7b` (best balance)
- Inference speed: ~10-20 tokens/sec
- **Good enough** for personal finance use

**Mac Mini M4 with 24GB RAM:**
- Models: `llama3.1:13b`, `qwen2.5:14b`, `gemma2:27b`
- Performance: Very good quality
- **Recommended model**: `qwen2.5:14b` (excellent quality)
- Inference speed: ~15-25 tokens/sec
- **Great choice** for privacy + quality

**Mac Studio M2 Ultra (64GB+ RAM):**
- Models: `qwen2.5:32b`, `llama3.1:70b` (4-bit quantized)
- Performance: Excellent quality
- Inference speed: ~20-40 tokens/sec
- **Best local option** without dedicated GPU

**Key Differences for Apple Silicon:**
- Uses **unified memory** (RAM = VRAM)
- No Docker GPU passthrough needed (Metal automatically used)
- Install Ollama natively on macOS (don't use Docker for Ollama)
- Neural Engine acceleration for some operations
- Generally 2-3x slower than equivalent NVIDIA GPU, but still very usable

**Mac Setup (Recommended):**
```bash
# Install Ollama directly on macOS (NOT in Docker)
brew install ollama

# Start Ollama service
ollama serve

# Pull a model (choose based on your RAM)
ollama pull qwen2.5:7b    # For 16GB Mac Mini M4
ollama pull qwen2.5:14b   # For 24GB Mac Mini M4

# Test the model
ollama run qwen2.5:7b
```

**Configure Sure to use local Ollama:**
```bash
# In your .env file
SURE_OPENAI_ACCESS_TOKEN=ollama-local
SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1  # Note: host.docker.internal for Mac
SURE_OPENAI_MODEL=qwen2.5:7b
```

**Why run Ollama natively on Mac instead of Docker?**
- ✅ Better performance (direct Metal access)
- ✅ Simpler setup (no GPU passthrough needed)
- ✅ Easier to manage models
- ✅ Lower memory overhead

**CPU-only (Intel/AMD without GPU):**
- Possible but 10-100x slower
- Not recommended for production use

### Docker Compose with Ollama

Add Ollama service to your deployment:

```yaml
services:
  sure-web:
    environment:
      OPENAI_ACCESS_TOKEN: ollama-local
      OPENAI_URI_BASE: http://sure-ollama:11434/v1
      OPENAI_MODEL: llama3.1:13b
    depends_on:
      - sure-ollama

  sure-worker:
    environment:
      OPENAI_ACCESS_TOKEN: ollama-local
      OPENAI_URI_BASE: http://sure-ollama:11434/v1
      OPENAI_MODEL: llama3.1:13b
    depends_on:
      - sure-ollama

  sure-ollama:
    image: ollama/ollama:latest
    container_name: sure-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ${SURE_DATA_DIR}/ollama:/root/.ollama
    # Uncomment for NVIDIA GPU support
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
    networks:
      - sure

  # Optional: Ollama WebUI for model management
  sure-ollama-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: sure-ollama-webui
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ${SURE_DATA_DIR}/ollama-webui:/app/backend/data
    environment:
      OLLAMA_BASE_URL: http://sure-ollama:11434
    depends_on:
      - sure-ollama
    networks:
      - sure
```

### Model Selection Guide

**For Chat Assistant (needs function calling):**

| Model | Size | VRAM | Quality | Speed | Best For |
|-------|------|------|---------|-------|----------|
| qwen2.5:32b | 32B | 24GB+ | Excellent | Medium | Best local option |
| llama3.1:13b | 13B | 16GB | Good | Fast | Balanced choice |
| gemma2:9b | 9B | 12GB | Good | Fast | Budget option |
| qwen2.5:7b | 7B | 8GB | Fair | Very Fast | Minimum viable |

**For Transaction Categorization:**

Any model that supports function calling will work. Categorization is less demanding than chat.

**Testing Models:**

Try different models to find what works for you:

```bash
# Pull and test multiple models
ollama pull llama3.1:13b
ollama pull qwen2.5:14b
ollama pull gemma2:9b

# Test each model
ollama run llama3.1:13b
# In chat: "Categorize this transaction: 'WHOLEFDS LAX' for $52.30"
```

### Ollama Commands

**List installed models:**
```bash
ollama list
```

**Pull a new model:**
```bash
ollama pull llama3.1:13b
```

**Remove a model:**
```bash
ollama rm llama3.1:13b
```

**Check Ollama status:**
```bash
curl http://localhost:11434/api/tags
```

**View model details:**
```bash
ollama show llama3.1:13b
```

## Privacy & Security Considerations

### What Data is Sent to LLM?

**For Transaction Categorization:**
- Transaction name/description
- Amount
- Date
- Your existing categories (for context)
- Transaction notes (if any)

**For Chat:**
- Your question
- Retrieved financial data (accounts, transactions, balances)
- Previous conversation context

**NOT sent:**
- Passwords or authentication tokens
- Other users' data
- Full transaction history (only relevant transactions)
- Account numbers or routing numbers

### Cloud AI Privacy

**OpenAI:**
- Data encrypted in transit (HTTPS)
- OpenAI's [data usage policy](https://openai.com/policies/usage-policies)
- API data not used for training (as of their policy)
- Data retention: 30 days

**Google Gemini:**
- Similar privacy policies
- Review [Google AI privacy](https://ai.google/responsibility/privacy/)

**Anthropic Claude:**
- Strong privacy focus
- Review [Anthropic usage policy](https://www.anthropic.com/legal/commercial-terms)

**Best Practices:**
- Use local AI for sensitive financial data
- Review provider privacy policies
- Be aware data leaves your infrastructure
- Consider regulatory requirements (GDPR, etc.)

### Local AI Privacy

**Complete Data Control:**
- All processing on your hardware
- No external API calls
- No data leaves your network
- Ideal for regulated environments

**Trade-offs:**
- Requires more powerful hardware
- Slower inference times
- Model quality may be lower
- More setup and maintenance

## Monitoring & Observability

### Langfuse Integration

Sure supports [Langfuse](https://langfuse.com/) for LLM observability:

**Setup:**
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

**What you can track:**
- All LLM requests and responses
- Token usage and costs
- Response latency
- Error rates
- User sessions

**Benefits:**
- Debug AI issues
- Optimize prompts
- Track costs
- Analyze usage patterns

**Dashboard Views:**
- Traces: Individual LLM calls
- Sessions: Full chat conversations
- Scores: Evaluate response quality
- Cost analysis: Track spending

### Debugging AI Issues

**Enable debug mode:**
```bash
AI_DEBUG_MODE=true
```

This shows AI reasoning in chat interface:
```
[Debug] Calling function: get_transactions
[Debug] Parameters: {"category": "Groceries", "date_range": "last_month"}
[Debug] Result: 18 transactions found, total $687.43
[Debug] Generating response...
```

**Common Issues:**

**Problem:** AI not categorizing correctly

**Solutions:**
- Review existing categories (AI learns from your data)
- Add transaction notes for context
- Use more specific category names
- Switch to a better model

**Problem:** Chat not understanding questions

**Solutions:**
- Be more specific in queries
- Break complex questions into steps
- Verify AI has access to needed functions
- Check model supports function calling

**Problem:** Slow responses

**Solutions:**
- Switch to faster model (e.g., gpt-4o-mini, gemini-flash)
- Use local AI with GPU
- Reduce context size (shorter conversations)

## Cost Optimization

### Strategies

**1. Hybrid Approach:**
- Local AI for bulk categorization
- Cloud AI for chat (lower volume)

**2. Model Selection:**
- Cheap model for simple tasks (categorization)
- Expensive model for complex reasoning (chat)

**3. Batch Processing:**
- Categorize transactions in batches (25-50 at a time)
- Reduces overhead per transaction

**4. Caching:**
- Sure caches AI responses for similar transactions
- Reduces duplicate API calls

**5. Rules Over AI:**
- Create rules for recurring transactions
- Only use AI for new/unknown transactions

### Cost Comparison

**Monthly Estimate (Personal Use):**

Assumptions: 150 transactions/month, 20 chat messages/month

| Provider | Categorization | Chat | Total/Month |
|----------|---------------|------|-------------|
| GPT-4.1 | $3-5 | $5-10 | $8-15 |
| GPT-4o-mini | $0.50 | $1-2 | $1.50-2.50 |
| Gemini Flash | $1-2 | $2-4 | $3-6 |
| Ollama (local) | $0* | $0* | ~$20** |

*No API costs
**Electricity costs (~$20-30/month for 24/7 GPU server)

**Break-even:**
If spending >$30/month on API calls, local AI becomes cost-effective (after hardware investment).

## Best Practices

### 1. Start with Cloud, Consider Local Later

- Begin with OpenAI for simplicity
- Monitor costs via Langfuse
- Switch to local if costs exceed $50-100/month

### 2. Optimize Categorization

- Create rules for recurring transactions (Netflix, rent, etc.)
- Only use AI for new or ambiguous transactions
- Review and approve AI suggestions initially

### 3. Write Clear Chat Queries

**Good:**
- "Show me my total spending on restaurants in December 2024"
- "Compare my grocery spending this month vs. last month"

**Bad:**
- "Spending?" (too vague)
- "Show me everything" (too broad)

### 4. Provide Context in Notes

For ambiguous transactions, add notes:
```
Transaction: "CVS Pharmacy $45.67"
Note: "Birthday card + toiletries"
Category: Shopping (not Healthcare)
```

AI will use this context for better categorization.

### 5. Regular Reviews

- **Weekly**: Review AI categorizations
- **Monthly**: Audit AI chat responses for accuracy
- **Quarterly**: Evaluate model performance and costs

## References

- [Sure AI Documentation](https://github.com/we-promise/sure/blob/main/docs/hosting/ai.md)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [OpenRouter](https://openrouter.ai/)
- [Langfuse](https://langfuse.com/)
- [Sure v0.6.6 Release Notes](https://github.com/we-promise/sure/releases/tag/v0.6.6)
