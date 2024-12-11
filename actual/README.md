# Actual

[Actual](https://actualbudget.com/) is a local-first personal finance tool. This configuration sets up a self-hosted instance of Actual Server.

## Configuration

Create a `.env` file in this directory:

```env
# Domain configuration
DOMAIN=actual.yourdomain.com

# Server configuration
ACTUAL_PORT=5006
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

## Notes

- The server will be available at `https://actual.yourdomain.com`
- Data is persisted in the configured data directory
- Make sure to save your sync key - you'll need it to connect clients to your server
- The web interface is served directly from the server
- Backup your data directory regularly!
