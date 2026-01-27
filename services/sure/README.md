# Sure <img src="https://github.com/we-promise/sure/raw/main/app/assets/images/logo.svg" width="24">

[Sure](https://github.com/we-promise/sure) is a self-hosted personal finance and budgeting application. It's a community fork of the archived Maybe Finance project.

Docker Image is from GitHub Container Registry, found [here](https://github.com/we-promise/sure/pkgs/container/sure).

## Architecture

Sure consists of four services:
- **sure-web**: Main web application (Rails)
- **sure-worker**: Background job processor (Sidekiq)
- **sure-db**: PostgreSQL database
- **sure-redis**: Redis cache for sessions and job queues

## Setup

1. **Create an `.env` file:**
   ```ini
   SURE_DOMAIN=sure.yourdomain.com
   SURE_PORT=3001
   SURE_DATA_DIR=${DATA_DIRECTORY}/sure
   SURE_POSTGRES_USER=sure_user
   SURE_POSTGRES_PASSWORD=<generate secure password>
   SURE_POSTGRES_DB=sure_production
   SURE_SECRET_KEY_BASE=<generate using: openssl rand -hex 64>
   ```

2. **Generate secure credentials:**
   ```bash
   # Generate SECRET_KEY_BASE
   openssl rand -hex 64

   # Generate a strong database password
   openssl rand -base64 32
   ```

3. **Run it:**
   ```bash
   docker compose up -d
   ```

4. Access Sure at `https://${SURE_DOMAIN}`

## Backups

Sure stores data in three locations:
- **Database**: PostgreSQL data at `${SURE_DATA_DIR}/postgres`
- **Storage**: File uploads at `${SURE_DATA_DIR}/storage`
- **Redis**: Cache data (can be regenerated)

```bash
# Backup database
docker exec sure-db pg_dump -U ${SURE_POSTGRES_USER} ${SURE_POSTGRES_DB} > sure-backup.sql

# Backup storage
tar -czf sure-storage.tar.gz -C ${SURE_DATA_DIR} storage

# Restore database
cat sure-backup.sql | docker exec -i sure-db psql -U ${SURE_POSTGRES_USER} -d ${SURE_POSTGRES_DB}
```

---

## Complete Configuration

### 1. AI Integration (Auto-Categorization)

Sure supports multiple AI providers for automatic transaction categorization.

**📚 Detailed Guide:** [AI Integration](docs/ai-integration.md) (Local Ollama or Cloud)

**Quick Config - Local AI (Recommended):**

> **Note:** Install Ollama natively on your host machine (not containerized) for best performance with Apple Silicon or GPU acceleration. See [Ollama Setup](docs/ollama-setup.md).

1. Install Ollama on your host: [ollama.com](https://ollama.com)

2. Run the setup script to configure the model:
   ```bash
   cd services/sure
   ./scripts/setup_model.sh
   ```

3. Add to your `.env`:
   ```ini
   SURE_OPENAI_ACCESS_TOKEN=ollama-local
   SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1
   SURE_OPENAI_MODEL=ryanliu6/ena:latest
   ```

4. Restart Sure and enable in UI:
   ```bash
   docker compose restart sure-web sure-worker
   ```
   Then go to **Settings → Self-Hosting → AI Provider → Enable**

**Quick Config - Cloud AI:**
```ini
# OpenRouter (access to Claude, GPT-4, Gemini, etc.)
SURE_OPENAI_ACCESS_TOKEN=sk-or-v1-your-key
SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
SURE_OPENAI_MODEL=anthropic/claude-sonnet-4.5
```

### 2. SimpleFIN Integration (Auto-Import Transactions)

SimpleFIN provides read-only bank syncing for $15/year.

**Setup Steps:**

1. **Create SimpleFIN account**: [beta-bridge.simplefin.org](https://beta-bridge.simplefin.org/)
   - Sign up ($15/year)
   - Add your financial institutions (chequing, credit cards, savings)
   - Generate a **Setup Token** (one-time use)

2. **Connect in Sure**:
   - Go to **Settings → Connections** (or **Accounts → Link Account**)
   - Select **SimpleFIN** as provider
   - Paste your Setup Token
   - Select accounts to sync

3. **Map accounts**: For each discovered account, create or link to a Sure account

**Limitations:**
- Max 90 days historical data
- Syncs once daily (time varies by bank)
- Read-only (cannot initiate transactions)

### 3. Enable Auto-Categorization

After AI and SimpleFIN are configured:

1. Go to **Settings → Transactions**
2. Set **Auto-categorize transactions** to "Always" or "Suggestions Only"
3. Enable **Merchant Enhancement** for cleaner merchant names

New transactions will now be automatically imported via SimpleFIN and categorized by AI.

---

## Using Sure Effectively

### Getting Started

1. **Create your first account**: Add your bank accounts, credit cards, and investment accounts
2. **Import transactions**: Use Plaid for automatic sync or import CSV files manually
3. **Set up categories**: Sure has default categories, but customize them to match your spending habits
4. **Create budgets**: Set monthly limits for categories you want to track

### Recommended Workflow

**Daily (2 min):**
- Review new transactions and fix any miscategorized ones
- The AI learns from your corrections

**Weekly (10 min):**
- Check budget progress in the dashboard
- Review spending by category
- Ask AI: "What unusual transactions happened this week?"

**Monthly (30 min):**
- Review month-over-month spending trends
- Adjust budgets based on actual spending
- Ask AI: "Compare my spending this month vs last month"
- Export data if needed for tax purposes

### Tips for Better Categorization

1. **Be consistent**: Always categorize similar transactions the same way
2. **Use rules**: Set up auto-categorization rules for merchants you use often
3. **Review AI suggestions**: The AI learns from your corrections, so fix mistakes early
4. **Split transactions**: Use split transactions for purchases that span categories (e.g., Costco groceries + gas)

### Data Privacy

- **Local AI (Ollama)**: Your transaction data never leaves your server
- **Cloud AI**: Transaction descriptions are sent to the AI provider, but not account numbers or balances
- **No external sync**: Sure doesn't share data with third parties (except Plaid for bank sync)

---

## Troubleshooting

### Sure Not Starting

**Symptoms:** Container exits immediately

**Solutions:**
1. Check logs: `docker logs sure-web -f`
2. Verify database is healthy: `docker ps | grep sure-db`
3. Check Redis is running: `docker ps | grep sure-redis`
4. Verify database credentials in `.env`

### Database Connection Failed

**Symptoms:** "Connection refused" or database errors

**Solutions:**
1. Check database logs: `docker logs sure-db`
2. Verify credentials match in `.env`
3. Check database is ready: `docker exec sure-db pg_isready`
4. On first run, wait for migrations to complete

### AI Not Working

**Symptoms:** Transactions not auto-categorizing

**Solutions:**
1. Verify API key in vault.yml
2. Check API key validity with provider
3. Review Sure logs: `docker logs sure-web | grep -i openai`
4. For Ollama: ensure `ollama serve` is running

### Migration Failed

```bash
# Run migrations manually
docker exec -it sure-web bundle exec rails db:migrate

# If database is corrupted, reset (LOSES DATA!)
docker volume rm nexus_sure_postgres
docker compose up -d
```

---

## Useful Commands

```bash
# View logs
docker logs sure-web -f
docker logs sure-worker -f
docker logs sure-db -f

# Restart Sure
docker restart sure-web sure-worker

# Access database shell
docker exec -it sure-db psql -U sure_user -d sure_production

# Run Rails console
docker exec -it sure-web bundle exec rails console

# Check database tables
docker exec -it sure-db psql -U sure_user -d sure_production -c "\dt"
```

### Delete Transactions by Date (Rails Console)

To delete all transactions before a certain date (e.g., starting fresh in 2026):

```bash
docker exec -it sure-web bundle exec rails console
```

```ruby
# Preview entries before 2026
old_entries = Entry.where("date < ?", Date.new(2026, 1, 1))
puts "Found #{old_entries.count} entries before 2026"

# Delete them
old_entries.destroy_all
```

Or via SQL for faster bulk deletion:

```bash
docker exec -it sure-db psql -U sure_user -d sure_production -c \
  "DELETE FROM entries WHERE date < '2026-01-01';"
```

---

## Notes

- **AI Costs**: Set appropriate spend limits on your AI provider account
- **Privacy**: Local AI (Ollama) keeps your data on your server; cloud AI sends transaction data to providers
- **First Run**: On first startup, Sure will automatically run database migrations (may take a few minutes)
- **Troubleshooting**: If database issues occur on initial setup, try removing the database volume: `docker volume rm nexus_sure_postgres`
