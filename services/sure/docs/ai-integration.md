# AI Integration & Automation

Complete guide to automating transaction imports and categorization in Sure.

## Overview

```
SimpleFIN (bank sync) → Sure imports transactions → AI auto-categorizes
```

| Component | Purpose |
|-----------|---------|
| **SimpleFIN** | Imports transactions from your banks ($15/year) |
| **AI Provider** | Categorizes transactions automatically |
| **Rules Engine** | Triggers auto-categorization on new transactions |

---

## Step 1: Set Up AI Provider

### Option A: Local AI (Ollama) - Recommended

Your data never leaves your server. Requires ~6GB RAM.

```bash
cd services/sure
./scripts/setup_model.sh
```

Add to `.env`:
```ini
SURE_OPENAI_ACCESS_TOKEN=ollama-local
SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1
SURE_OPENAI_MODEL=ryanliu6/ena:latest
```

See [Ollama Setup Guide](ollama-setup.md) for customizing the model with your categories.

### Option B: Cloud AI (OpenRouter)

Single API for multiple providers. Data is sent to the provider.

1. Get API key from [openrouter.ai](https://openrouter.ai/)
2. Add to `.env`:
   ```ini
   SURE_OPENAI_ACCESS_TOKEN=sk-or-v1-your-key
   SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
   SURE_OPENAI_MODEL=anthropic/claude-sonnet-4.5
   ```

**Model options:**
| Model | Cost | Notes |
|-------|------|-------|
| `deepseek/deepseek-chat` | ~$2-5/mo | Cheapest, good quality |
| `google/gemini-flash-1.5` | ~$3-8/mo | Fast |
| `anthropic/claude-sonnet-4.5` | ~$10-20/mo | Best reasoning |

### Enable AI in Sure

```bash
docker compose restart sure-web sure-worker
```

Then: **Settings → Self-Hosting → AI Provider → Enable**

---

## Step 2: Set Up SimpleFIN (Bank Sync)

SimpleFIN provides read-only bank syncing for $15/year.

### Create Account

1. Go to [beta-bridge.simplefin.org](https://beta-bridge.simplefin.org/)
2. Sign up and add your financial institutions
3. Generate a **Setup Token** (one-time use)

### Connect in Sure

1. Go to **Settings → Connections** (or **Accounts → Link Account**)
2. Select **SimpleFIN** as provider
3. Paste your Setup Token
4. Select accounts to sync
5. Map each discovered account to a Sure account

**Limitations:**
- Max 90 days historical data on initial sync
- Syncs automatically (frequency varies by bank)
- Read-only (cannot initiate transactions)

---

## Step 3: Enable Auto-Categorization

Create a Rule to automatically categorize new transactions.

1. Go to **Settings → Transactions → Rules**
2. Click **New Rule**
3. Add condition: **Category** → **is empty** (only categorize uncategorized)
4. Add action: **Auto Categorize**
5. Save the rule
6. Optionally: Enable "Run automatically" to categorize as transactions arrive

**Tip:** Create deterministic rules first for known merchants (Netflix → Entertainment), then use AI for the rest.

---

## Complete Automation Flow

Once configured:

```
1. Bank transaction occurs
2. SimpleFIN syncs it to Sure (usually within 24h)
3. Rule triggers: "Category is empty"
4. AI analyzes transaction and assigns category
5. You review in dashboard (optional)
```

### Recommended Workflow

**Daily (2 min):** Review new transactions, fix any miscategorizations (AI learns from corrections)

**Weekly:** Check budget progress, ask AI: "What unusual transactions happened this week?"

---

## AI Chat Assistant

Ask questions about your finances:

```
"How much did I spend on groceries last month?"
"What subscriptions am I paying for?"
"Compare my spending this month vs last month"
"Which categories am I overspending in?"
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| AI not categorizing | Verify API key, check `docker logs sure-web \| grep -i openai` |
| SimpleFIN not syncing | Check connection in Settings → Connections |
| Wrong categories | Add transaction notes for context, AI uses them |
| Ollama slow/not responding | Ensure Ollama is running: `ollama list` |

---

## Privacy

**Local AI (Ollama):** Data never leaves your server.

**Cloud AI:** Transaction details (merchant, amount, date) are sent to the provider. Account numbers and passwords are NOT sent. See provider privacy policies:
- [Anthropic](https://www.anthropic.com/legal/privacy) - Zero retention for API calls
- [OpenAI](https://openai.com/policies/privacy-policy) - 30 day retention
- [Deepseek](https://platform.deepseek.com/) - China-based
