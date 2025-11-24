# Actual

[Actual](https://actualbudget.com/) is a local-first personal finance tool. This configuration sets up a self-hosted instance of Actual Server.

## Configuration

Create a `.env` file in this directory:

```env
# Domain configuration
ACTUAL_DOMAIN=actual.yourdomain.com

# Server configuration
ACTUAL_SYNC_KEY=your_secure_sync_key_here

# Optional: Custom data directory
ACTUAL_DATA_DIR=${DATA_DIRECTORY}/actual
```

## Usage

### Standalone
```bash
docker compose up -d
```

### With generate_compose.py
```bash
./generate_compose.py actual
```

## Updates
This container will have its image automatically updated via [watchtower](../watchtower/).

## Backups
Data for Actual is stored at the configured `ACTUAL_DATA_DIR`, and should be backed up regularly using standard filesystem backup tools.

## Notes
- The server will be available at `https://actual.yourdomain.com`
- Data is persisted in the configured data directory
- Make sure to save your sync key - you'll need it to connect clients to your server
- The web interface is served directly from the server
