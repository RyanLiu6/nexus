# TeslaMate

Self-hosted Tesla telemetry logger and MQTT streamer (`teslamate/teslamate` + `postgres:17`), used to feed live vehicle location and drive state into Home Assistant for arrival automations.

## Architecture

- **TeslaMate (`teslamate:4000`):** Connects to Tesla's Streaming API when driving (sleeping cleanly when parked) and publishes live vehicle topics (`teslamate/cars/1/*`) to Home Assistant's Mosquitto MQTT broker.
- **PostgreSQL (`teslamate-db`):** Stores drive history, geofences, and encrypted tokens under `${NEXUS_DATA_DIRECTORY}/Config/teslamate/postgres`.
- **Routing:** Exposed via Traefik at `https://teslamate.${NEXUS_DOMAIN}` with `internal-chain@file` (switch to `authentik-chain@file` once a Proxy Provider is added in Authentik).

## Configuration

Required keys in `config/secrets.enc.yml` (see `config/secrets.sample.yml`):
- `teslamate_encryption_key` — 32-byte hex key (`openssl rand -hex 32`)
- `teslamate_postgres_user`, `teslamate_postgres_password`, `teslamate_postgres_db`
- `teslamate_mqtt_host`, `teslamate_mqtt_username`, `teslamate_mqtt_password`

## First-Time Sign-In

1. Deploy the service (`invoke deploy --preset home`).
2. Generate Tesla access & refresh tokens locally (e.g. via [tesla_auth](https://github.com/adriankumpf/tesla_auth) or a mobile token app).
3. Open `https://teslamate.${NEXUS_DOMAIN}` and paste the tokens.
4. Restart the container once after signing in (`docker restart teslamate`) so the MQTT publisher attaches to the newly discovered vehicle.
