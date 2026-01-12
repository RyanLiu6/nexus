# Authentication (Authelia)

Authelia is an open-source authentication and authorization server providing two-factor authentication and single sign-on (SSO).

## Setup
1. Create `.env` from sample.
2. **Important:** Copy the sample config files in the root of `auth/` to your `DATA_DIRECTORY/config/authelia/` (create this folder).
   - `configuration.yml`
   - `users_database.yml`
3. **Important:** Generate a password hash for your user using:
   `docker run authelia/authelia:latest authelia crypto hash generate argon2 --password 'yourpassword'`
   Update `users_database.yml` with this hash.
4. Run `docker compose up -d`.

