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

## 2. Create Your Custom Model

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

## 3. Test Your Model

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

## 4. Configure Sure

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

## 5. Inputting Transactions

Sure supports multiple ways to get transactions in:

1. **Bank Sync**: via Plaid or GoCardless (requires API keys).
2. **File Import**: Upload CSV/OFX/QIF files from your bank.
3. **Manual Entry**:
   - Go to **Transactions**.
   - Click **+ New Transaction**.
   - Enter details manually. The AI will still attempt to categorize these based on the Merchant Name you type!

## Troubleshooting

- **Connection Refused?**
  Ensure Ollama is running (`Ollama` in menu bar).
  Ensure `OLLAMA_ORIGINS` allows browser access if using the web UI, though for Sure backend-to-Ollama, `host.docker.internal` usually bypasses this.
  If needed, run: `launchctl setenv OLLAMA_HOST "0.0.0.0"` to make Ollama listen on all interfaces.

- **Model not found?**
  Run `ollama list` to verify `ryanliu6/ena:latest` exists.
