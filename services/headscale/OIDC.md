# Headscale OIDC Authentication

Headscale natively supports OpenID Connect (OIDC). Enabling OIDC allows users and devices to sign in using their identity provider directly in the browser when running `tailscale up`, exactly like standard Tailscale SaaS.

This guide focuses on setting up **Google** as the OIDC provider.

## Cost Analysis

- **Google Cloud OAuth 2.0 / OpenID Connect is 100% Free ($0.00)**.
- Google does not charge for OAuth 2.0 Web Client authentication or basic profile verification (`openid`, `profile`, `email`).
- There are no monthly fees, API quotas that incur costs, or credit card requirements for basic Google OAuth consent screens.

## Step-by-Step Setup Guide (Google Workspace / Gmail)

### 1. Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `Nexus Homelab`).

### 2. Configure the Google Auth Platform (formerly OAuth Consent Screen)
Google recently updated their UI to the "Google Auth Platform".

1. In the sidebar, navigate to **APIs & Services** > **Google Auth Platform** (or click "OAuth consent screen" which redirects here).
2. On the **Overview** page, click **Get Started** (if prompted).
3. **Audience**:
   - Select **External** (or **Internal** if using a custom Google Workspace domain).
   - Under **Test Users** (if External), add your Google email address(es) that will be allowed to log in.
   - Click **Save**.
4. **Branding**:
   - **App name**: `Nexus Headscale`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
   - Under **App domains**, use your GitHub repo links to satisfy Google's corporate requirements without triggering mandatory domain ownership verification:
     - **Application home page**: `https://github.com/ryanliu6/nexus`
     - **Privacy policy link**: `https://github.com/ryanliu6/nexus/blob/main/services/headscale/PRIVACY.md`
     - **Terms of service link**: `https://github.com/ryanliu6/nexus/blob/main/services/headscale/TOS.md`
   - Under **Authorized domains**, type `github.com` and hit Enter.
   - Click **Save**.
5. **Data Access** (Scopes):
   - Click **Add or Remove Scopes**.
   - Select or manually add:
     - `.../auth/userinfo.email`
     - `.../auth/userinfo.profile`
     - `openid`
   - Click **Save**.
6. **Publish to Production (Crucial)**:
   - Go back to the **Overview** tab.
   - Click **Publish App** to move the app from Testing to Production.
   - *Why?* If you leave the app in "Testing" mode, Google will expire your authentication tokens every 7 days, forcing your nodes to constantly re-authenticate. Because you are only requesting basic profile scopes, publishing will not trigger a manual Google verification review.

### 3. Create OAuth 2.0 Client Credentials
1. In the sidebar, go to **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** > **OAuth client ID**.
3. Set **Application type** to **Web application**.
4. Set **Name** to `Headscale OIDC`.
5. Under **Authorized redirect URIs**, click **+ Add URI** and enter your Headscale callback URL:
   ```text
   https://headscale.<your-domain>/oidc/callback
   ```
   *(Replace `<your-domain>` with your actual Nexus domain, e.g., `https://headscale.example.com/oidc/callback`)*
6. Click **Create**.
7. Copy the generated **Client ID** and **Client Secret**.

### 4. Configure Headscale

Instead of hardcoding your secrets into `config.yaml` where they would be exposed in Git, Nexus injects them securely via Ansible Vault.

1. Open your encrypted vault:
   ```bash
   inv secrets.edit
   ```
2. Add your Google OAuth credentials:
   ```yaml
   headscale_oidc_client_id: "<YOUR_GOOGLE_CLIENT_ID>"
   headscale_oidc_client_secret: "<YOUR_GOOGLE_CLIENT_SECRET>"
   ```
   Save and close the vault.

3. Update the `oidc` section in `services/headscale/config.yaml` to whitelist your users:

```yaml
oidc:
  only_start_if_oidc_is_available: true
  issuer: "https://accounts.google.com"
  # client_id and client_secret are provided securely via vault/env vars
  scope: ["openid", "profile", "email"]
  strip_email_domain: false

  # Note: You can restrict who can log in by their domain or specific email.
  # If left empty/undefined, any valid Google account might be able to authenticate.

  allowed_domains: [] # e.g. ["example.com"] to restrict to a Google Workspace domain

  allowed_users:
    - "<your-email>@gmail.com" # Whitelist specific Google accounts
```

*Note: Headscale's implementation validates the user based on `allowed_domains` and `allowed_users`.*

### 5. Restart Headscale

Deploy the updated configuration using the Nexus CLI:

```bash
inv deploy --service headscale
```

### 6. Sign In on Devices

Once the service is back up, users can connect with:

```bash
tailscale up --login-server https://headscale.<your-domain>
```

Tailscale will provide a web link that opens Google's standard login page. Once authenticated, the node is immediately registered to Headscale and will appear in Headplane and the CLI.
