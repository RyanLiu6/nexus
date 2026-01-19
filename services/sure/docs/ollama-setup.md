# Ollama Setup: Native App & Custom Models

This guide explains how to set up **Native Ollama** (recommended for macOS) and create a **Custom Model** with your specific financial categories and rules.

Using a native installation allows Ollama to directly access your hardware (Apple Silicon Neural Engine/GPU) for the best possible performance.

## 1. Install Native Ollama

### macOS (Recommended)
1. Download and install from [ollama.com](https://ollama.com/download/mac).
2. Or use Homebrew:
   ```bash
   brew install --cask ollama
   ```
3. Start the application. You should see the Ollama icon in your menu bar.

### Linux / Windows
Follow instructions at [ollama.com](https://ollama.com).

## 2. Quick Setup (Recommended)

A setup script automates model creation, base model pulling, and memory configuration:

```bash
cd services/sure
./scripts/setup_model.sh
```

The script will:
1. Check that Ollama is installed and running (starts it if needed)
2. Configure `OLLAMA_KEEP_ALIVE=-1` so the model stays loaded in memory
3. Pull the base model (`qwen3:8b`)
4. Create the custom model `ryanliu6/ena:latest` from the `Modelfile`
5. Verify the model with a test categorization

After the script completes, skip to [Section 5: Configure Sure](#5-configure-sure).

## 3. Manual Model Creation

If you prefer manual setup or the script doesn't work for your environment, follow these steps.

We will create a custom model named `ryanliu6/ena:latest`. This model embeds your specific categories and rules directly into the AI, ensuring consistent categorization.

1. **Locate the Modelfile**:
   A file named `Modelfile` is located in the `sure/` directory of this project.

2. **Customize Categories (Optional)**:
   Open `sure/Modelfile` and edit the categories list to match your actual budget. You can add specific rules for merchants you frequent.

3. **Build the Model**:
   Open your terminal, navigate to the `sure` directory, and run:

   ```bash
   # Pull the base model first (we use qwen3:8b for speed/quality balance)
   ollama pull qwen3:8b

   # Create your custom model
   ollama create ryanliu6/ena:latest -f Modelfile
   ```

   *Success! You now have a specialized financial AI model running locally.*

## 4. Test Your Model

Before connecting Sure, verify your model understands your categories.

Run this command in your terminal:

```bash
ollama run ryanliu6/ena:latest "Categorize this transaction: 'TST* SQ *THE COFFEE BEAN' for $14.50"
```

**Expected Output:**
```json
{
  "merchant": "The Coffee Bean",
  "category": "Food: Coffee & Snacks",
  "confidence": "high",
  "reasoning": "Identified coffee shop chain"
}
```

## 5. Configure Sure

Now tell Sure to use your new custom model.

1. **Edit `.env` file**:
   Update the AI configuration section in `sure/.env`:

   ```ini
   # Use 'ryanliu6/ena:latest' model we just created
   SURE_OPENAI_ACCESS_TOKEN=ollama-local
   SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1
   SURE_OPENAI_MODEL=ryanliu6/ena:latest
   ```

   *Note: `host.docker.internal` allows the Docker container to talk to the Ollama app running natively on your Mac.*

2. **Restart Sure**:
   ```bash
   docker compose restart sure-web sure-worker
   ```

3. **Enable in UI**:
   - Go to **Settings > Self-Hosting > AI Provider**.
   - Click **Save/Enable**.

## 6. Inputting Transactions

Sure supports multiple ways to get transactions in:

1. **Bank Sync**: via SimpleFIN, Plaid, or GoCardless
2. **File Import**: Upload CSV/OFX/QIF files from your bank
3. **Manual Entry**: Go to **Transactions** → **+ New Transaction**

**Note:** Transactions are NOT automatically categorized on import. To use AI categorization, create a Rule with the **Auto Categorize** action (see [AI Integration](ai-integration.md#1-automatic-transaction-categorization)).

## 7. Memory Management (KEEP_ALIVE)

By default, Ollama unloads models from memory after 5 minutes of inactivity. For fast AI responses when running categorization Rules, the `setup_model.sh` script configures `OLLAMA_KEEP_ALIVE=-1` which keeps the model permanently loaded.

### Memory Impact

| Setting | Behavior | RAM Usage | Best For |
|---------|----------|-----------|----------|
| `5m` (default) | Unload after 5 minutes idle | ~0GB when idle | Occasional use |
| `1h` | Unload after 1 hour idle | ~6GB for up to 1 hour | Moderate use |
| `2h` | Unload after 2 hours idle | ~6GB for up to 2 hours | Frequent use |
| `-1` (configured) | Never unload | ~6GB always | Always-on server |

**Mac Mini M4 (16GB RAM) with KEEP_ALIVE=-1:**
```
├── Ollama model (ena):  ~6GB
├── Sure + services:     ~2-3GB
├── macOS + apps:        ~3-4GB
└── Available:           ~4-5GB (70-75% usage)
```

### Monitoring Alerts

The monitoring stack has alerts configured for memory usage:
- **Warning**: >75% memory usage for 10 minutes
- **Critical**: >95% memory usage for 5 minutes

With the model always loaded, typical memory sits around 70-75%, leaving headroom before alerts fire.

### Verifying Model State

Check if the model is loaded in memory:
```bash
curl -s http://localhost:11434/api/ps | jq
```

Output when loaded:
```json
{
  "models": [{
    "name": "ryanliu6/ena:latest",
    "size": 5537000000
  }]
}
```

### Manual KEEP_ALIVE Configuration

If you need to change the setting manually:

**Set to a specific value (e.g., 1h, 2h, -1):**
```bash
# Edit the plist file
nano ~/Library/LaunchAgents/environment.ollama.plist
# Change the value in <string>-1</string> to your preferred setting (e.g., "1h", "2h")

# Reload and restart
launchctl unload ~/Library/LaunchAgents/environment.ollama.plist
launchctl load ~/Library/LaunchAgents/environment.ollama.plist
pkill -f "Ollama" && open -a Ollama
```

**Quick set for current session only:**
```bash
launchctl setenv OLLAMA_KEEP_ALIVE "1h"  # or "2h", "-1", "5m"
pkill -f "Ollama" && open -a Ollama
```

**Revert to default (5 minutes):**
```bash
launchctl unload ~/Library/LaunchAgents/environment.ollama.plist
rm ~/Library/LaunchAgents/environment.ollama.plist
pkill -f "Ollama" && open -a Ollama
```

## Troubleshooting

- **Connection Refused?**
  Ensure Ollama is running (`Ollama` in menu bar).
  Ensure `OLLAMA_ORIGINS` allows browser access if using the web UI, though for Sure backend-to-Ollama, `host.docker.internal` usually bypasses this.
  If needed, run: `launchctl setenv OLLAMA_HOST "0.0.0.0"` to make Ollama listen on all interfaces.

- **Model not found?**
  Run `ollama list` to verify `ryanliu6/ena:latest` exists.
