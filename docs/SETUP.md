# Authentik & Headscale OIDC Integration Guide

This document summarizes the specific configurations applied to both Pyinfra and the Authentik Web UI. It serves as a master checklist for setting up Authentik as the central IdP, federating with Google, and allowing Headscale/Headplane to authenticate users without changing their base Authentik username.

## Phase 1: Google Federation & Enrollment

### 1. Google OIDC Federation
- Configured a **Google Social Login Source** in Authentik.
- Users authenticate via Google instead of creating local passwords.

### 2. Enrollment Flow & Whitelist
- Created/updated custom **Flows and Stages** to handle the Google OIDC enrollment.
- Implemented a **Whitelist Policy** attached to the enrollment flow. This Python policy ensures that only authorized Google accounts (e.g., specific email addresses) are allowed to create an Authentik account, instantly rejecting unauthorized users.

### 3. Profile Picture Mapping
- Created a **Custom Property Mapping** to extract the Google profile picture (`picture` claim) and settings from the Google OIDC source and map them to the local Authentik user profile.

---

## Phase 2: The Headscale "Username & Verification" Quirk

### The Problem
1. **Tailscale strictness:** Tailscale's ACL compiler strictly requires usernames to contain an `@` symbol (i.e., an email address).
2. **Authentik defaults:** Authentik maps OIDC `preferred_username` to the user's base username (e.g., `ryanliu6`), lacking the required `@` symbol.
3. **Email Verification:** In recent versions of Authentik (2025.10+), the `email_verified` claim defaults to `False` for federated logins. Headscale rejects unverified emails by default.

### The Solution (Authentik UI)

You created a **Custom Property Mapping** in Authentik to inject the correct claims specifically for Headscale:

1. **Customization -> Property Mappings**
   - **Type:** OAuth2/OpenID Scope Mapping
   - **Name:** `Map Email to preferred_username`
   - **Scope Name:** `headscale-username`
   - **Expression:**
     ```python
     return {
         "preferred_username": request.user.email,
         "email_verified": True
     }
     ```

### Applications and Providers
You configured the **Applications and Providers** in Authentik to use this new mapping:
1. Created Applications for **Headscale** and **Headplane**.
2. Created corresponding **OAuth2/OpenID Providers**.
3. Under **Advanced protocol settings -> Scopes** for both providers, you explicitly selected the `Map Email to preferred_username` mapping.

---

## Phase 3: Pyinfra Infrastructure Changes

To ensure the apps requested this new custom mapping and allowed the correct emails, the underlying infrastructure code was updated:

1. **Headscale Config (`templates/headscale-config.yaml.j2`)**
   - Added `"headscale-username"` to the OIDC `scope` array.
2. **Headplane Config (`services/headscale/docker-compose.yml`)**
   - Enabled environment overrides (`HEADPLANE_LOAD_ENV_OVERRIDES=true`).
   - Appended `headscale-username` to the `HEADPLANE_OIDC__SCOPE` environment variable.
3. **Headscale ACLs (`config/secrets.enc.yml`)**
   - Ensured `tailscale_users.admins` explicitly lists the verified email (e.g., `dio.ryanliu@gmail.com`) so Headscale's internal firewall permits the connection.

---

## Phase 4: Headscale & Headplane Bug Fixes

During this integration, a few undocumented edge cases and crashes in Headscale and Headplane were resolved in the Pyinfra codebase:

1. **Headplane "Invalid URL" Startup Crash**
   - Headplane crashes on boot if the URL environments aren't completely specified.
   - **Fix:** Explicitly set `ORIGIN=https://headplane.${NEXUS_DOMAIN}` and `HEADPLANE_SERVER__BASE_URL=https://headplane.${NEXUS_DOMAIN}` in the docker-compose template.
2. **Headscale Compiler Crash on Empty ACL Groups**
   - Tailscale's `hujson` compiler panics if an ACL block references a group that has no members.
   - **Fix:** Added Jinja2 conditional logic to `templates/acl.hujson.j2` to completely omit the `group:members` block if the member list in `secrets.enc.yml` is empty.

---

## Operational Notes (Docker Compose)

**Crucial Step:** When Pyinfra updates Headscale's `config.yaml` or `acl.hujson`, simply running `inv deploy` (which runs `docker compose up -d`) **will not restart the Headscale container**. Docker Compose only detects changes to the `docker-compose.yml` definition, not host-mounted files.

To ensure Headscale loads the new OIDC scopes and configuration:
```bash
# Force the container to restart and pick up the new config.yaml
docker restart headscale
```
Failure to restart the container will result in Headscale using outdated OIDC scopes, causing it to fall back to Authentik's default behavior (stripping the email verification and using the base username).

## Phase 5: Apps, Policies, & Dashboard Replacement

We replaced the legacy custom `homepage` and `dashboard` with the native **Authentik Application Dashboard**. This acts as the centralized launchpad for all services.

### Application Definitions & Proxy Providers
Each internal app is protected and integrated via Authentik:
1. **Proxy Providers**: For apps that don't natively support OIDC, we created Authentik Proxy Providers. These providers intercept requests, authenticate the user, and then forward the request to the application.
2. **Applications**: We created UI applications in Authentik for each provider. We assigned these applications to groups (e.g., `Media`, `Infrastructure`) for UI organization in the Authentik dashboard.

### Access Control Policies (Zero Trust by Default)
To ensure strict security, we implemented a "Deny by Default" strategy using Authentik Policies and Bindings:
- **Default Admin Binding**: We created a Python automation (`bind_admins.py`) that binds the `Admins` group to **every** application.
- **Explicit Member Access**: The `Admins` group gets access to everything by default. Regular members are strictly denied access unless explicitly bound to a specific application or provider.
- **UI Visibility**: By default, the Authentik Application Dashboard only displays applications that the logged-in user is explicitly authorized to access via Policy Bindings. Users cannot see apps they do not have access to, providing a clean and secure UI experience.
