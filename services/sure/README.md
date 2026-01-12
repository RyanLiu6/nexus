# Sure
[Sure](https://github.com/we-promise/sure) is a self-hosted personal finance and budgeting application. It's a community fork of the archived Maybe Finance project.

Docker Image is from GitHub Container Registry, found [here](https://github.com/we-promise/sure/pkgs/container/sure).

## Architecture
Sure consists of four services:
- **sure-web**: Main web application (Rails)
- **sure-worker**: Background job processor (Sidekiq)
- **sure-db**: PostgreSQL database
- **sure-redis**: Redis cache for sessions and job queues

## Setup
1. Create an `.env` file based on `.env.sample`:
```ini
SURE_DOMAIN=sure.yourdomain.com
SURE_PORT=3001
SURE_DATA_DIR=${DATA_DIRECTORY}/sure
SURE_POSTGRES_USER=sure_user
SURE_POSTGRES_PASSWORD=<generate secure password>
SURE_POSTGRES_DB=sure_production
SURE_SECRET_KEY_BASE=<generate using: openssl rand -hex 64>
SURE_OPENAI_ACCESS_TOKEN=<optional, for AI features>
```

2. Generate secure credentials:
```bash
# Generate SECRET_KEY_BASE
openssl rand -hex 64

# Generate a strong database password
openssl rand -base64 32
```

3. Run it!
```bash
docker compose up -d
```

4. Access Sure at `https://${SURE_DOMAIN}` (or `http://localhost:${SURE_PORT}` for local testing)


## Backups
Sure stores data in three locations:
- **Database**: PostgreSQL data at `${SURE_DATA_DIR}/postgres`
- **Storage**: File uploads at `${SURE_DATA_DIR}/storage`
- **Redis**: Cache data at `${SURE_DATA_DIR}/redis`

To backup the database and storage (Redis is cache and can be regenerated):
```bash
# Backup database
0 2 * * * docker exec sure-db pg_dump -U ${SURE_POSTGRES_USER} ${SURE_POSTGRES_DB} > ${DATA_DIRECTORY}/Backups/sure/`date +\%F`-db.sql

# Backup storage files
0 2 * * * tar -czf ${DATA_DIRECTORY}/Backups/sure/`date +\%F`-storage.tar.gz -C ${SURE_DATA_DIR} storage
```

## AI Integration

Sure supports multiple AI providers for automatic transaction categorization and financial insights:

### Recommended Setup

**1. Local AI with Ollama (Best for Privacy)**
- Cost: $0/month (uses your hardware)
- Privacy: Complete (data never leaves your server)
- Setup: See [Ollama Setup Guide](docs/ollama-setup.md)
- Recommended for: Mac Mini M4 users, privacy-focused users

**2. Cloud AI Options**
- **Deepseek**: $2-5/month, good quality
- **Claude API**: $10-25/month, best reasoning (separate from Pro subscription)
- **Gemini API**: $3-10/month, fast and affordable
- **OpenAI**: $5-20/month, most reliable

**3. OpenRouter (Most Flexible)**
- Single API key for all providers
- Easy switching between models
- Cost tracking and failover
- Setup: See [AI Integration Guide](docs/ai-integration.md)

### Quick AI Setup

```bash
# For Ollama (local AI)
SURE_OPENAI_ACCESS_TOKEN=ollama-local
SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1
SURE_OPENAI_MODEL=qwen2.5:7b

# For Claude API
SURE_OPENAI_ACCESS_TOKEN=sk-ant-your-key
SURE_OPENAI_URI_BASE=https://api.anthropic.com/v1
SURE_OPENAI_MODEL=claude-sonnet-4-20250514

# For OpenRouter (any provider)
SURE_OPENAI_ACCESS_TOKEN=sk-or-v1-your-key
SURE_OPENAI_URI_BASE=https://openrouter.ai/api/v1
SURE_OPENAI_MODEL=deepseek/deepseek-chat
```

**Important**: Web subscriptions (Claude Pro, Gemini Pro) do not provide API access. You need separate API keys for Sure.

## Notes
- **AI Costs**: Set appropriate spend limits on your AI provider account
- **Privacy**: Local AI (Ollama) keeps your data on your server; cloud AI sends transaction data to providers
- **First Run**: On first startup, Sure will automatically run database migrations. This may take a few minutes.
- **Troubleshooting**: If you encounter database connection issues on initial setup, try removing the database volume: `docker volume rm nexus_sure_postgres`
