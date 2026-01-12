# Backups (Borgmatic)

Automated backups using Borgmatic.

## Setup
1. Create `.env`.
2. Create a `config.yaml` in `backups/config/` (see Borgmatic docs).
3. Initialize the repo: `docker compose run --rm borgmatic rcreate --encryption repokey`.
4. Run: `docker compose up -d`.

