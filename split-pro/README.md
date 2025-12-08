# Split-Pro

[Split-Pro](https://github.com/oss-apps/split-pro) is an open-source expense sharing application. This configuration sets up a self-hosted instance of Split-Pro with PostgreSQL.

## Configuration

Create a `.env` file in this directory:

```env
# Domain configuration
SPLITPRO_DOMAIN=splitpro.yourdomain.com

# Port configuration
SPLITPRO_PORT=3000

# Timezone
TIMEZONE=America/Vancouver

# Database configuration
POSTGRES_USER=splitpro
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=splitpro
POSTGRES_PORT=5432

# NextAuth configuration
NEXTAUTH_SECRET=your_nextauth_secret_here

# Google OAuth configuration (optional but recommended)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Optional: Custom data directory
SPLITPRO_DATA_DIR=${DATA_DIRECTORY}/splitpro
```

## Usage

### Standalone
```bash
docker compose up -d
```

### With generate_compose.py
```bash
./generate_compose.py splitpro
```

## Updates
This container will have its image automatically updated via [watchtower](../watchtower/).

## Backups
Database data is stored in the volume mounted at `${SPLITPRO_DATA_DIR}/database`. The PostgreSQL data should be backed up regularly using standard filesystem backup tools or PostgreSQL backup utilities.

## Notes
- The application will be available at `https://splitpro.yourdomain.com`
- A PostgreSQL database is automatically created and managed by the postgres service
- Google OAuth is optional but recommended for user authentication
- Make sure to generate a strong `NEXTAUTH_SECRET` - you can use: `openssl rand -base64 32`
- The application uses the internal `splitpro` network for database communication and the `proxy` network for Traefik routing
