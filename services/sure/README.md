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

## AI Integration

Sure supports multiple AI providers for automatic transaction categorization.

### Option 1: Local AI with Ollama (Recommended for Privacy)

Keep your financial data completely private:

```bash
# Install Ollama (macOS)
brew install ollama

# Pull base model and create custom financial model
ollama pull qwen3:7b
ollama create ena -f Modelfile
```

Configure in vault.yml:
```yaml
sure_openai_access_token: "ollama-local"
sure_openai_uri_base: "http://host.docker.internal:11434/v1"
sure_openai_model: "ena"
```

**Full Instructions:** [Ollama Setup Guide](docs/ollama-setup.md)

### Option 2: Cloud AI Providers

```yaml
# OpenAI
sure_openai_access_token: "<openai_api_key_here>"
sure_openai_model: "gpt-4"

# Claude API
sure_openai_access_token: "<anthropic_api_key_here>"
sure_openai_uri_base: "https://api.anthropic.com/v1"
sure_openai_model: "claude-sonnet-4-20250514"

# OpenRouter (any provider)
sure_openai_access_token: "<openrouter_api_key_here>"
sure_openai_uri_base: "https://openrouter.ai/api/v1"
sure_openai_model: "deepseek/deepseek-chat"
```

**Full Instructions:** [AI Integration Guide](docs/ai-integration.md)

### Cost Comparison

| Provider | Monthly Cost | Privacy |
|----------|--------------|---------|
| Ollama (local) | $0 | ✅ Complete |
| Deepseek | $2-5 | ❌ Cloud |
| Claude API | $10-25 | ❌ Cloud |
| OpenAI | $5-20 | ❌ Cloud |

**Important**: Web subscriptions (Claude Pro, Gemini Pro) do NOT provide API access.

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

---

## Notes

- **AI Costs**: Set appropriate spend limits on your AI provider account
- **Privacy**: Local AI (Ollama) keeps your data on your server; cloud AI sends transaction data to providers
- **First Run**: On first startup, Sure will automatically run database migrations (may take a few minutes)
- **Troubleshooting**: If database issues occur on initial setup, try removing the database volume: `docker volume rm nexus_sure_postgres`
