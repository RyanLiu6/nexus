# Ollama Setup for Local AI

Complete guide for setting up Ollama for local AI with Sure. This provides complete privacy - your financial data never leaves your infrastructure.

## Why Ollama?

**Benefits:**
- ✅ **$0 per month** (no API fees)
- ✅ **Complete privacy** - data never leaves your server
- ✅ **Works offline**
- ✅ **Good enough quality** for personal finance
- ✅ **No vendor lock-in**

**Trade-offs:**
- ⚠️ Requires hardware investment
- ⚠️ Slightly slower than cloud AI
- ⚠️ Quality not quite as good as GPT-4/Claude
- ⚠️ Setup and maintenance required

## Hardware Requirements

### Apple Silicon (Mac M1/M2/M3/M4)

**✨ Recommended for Mac users!** Apple Silicon has excellent ML performance using unified memory.

**Mac Mini M4 Base (16GB RAM):**
- ✅ `qwen2.5:7b` - Recommended balance
- ✅ `gemma2:9b` - Better quality, slower
- ✅ `llama3.2:3b` - Fastest, basic quality
- Performance: ~10-20 tokens/sec (good for personal finance)

**Mac Mini M4 with 24GB RAM:**
- ✅ `qwen2.5:14b` - Excellent quality, recommended
- ✅ `llama3.1:13b` - Very good quality
- Performance: ~15-25 tokens/sec (excellent)

**Mac Studio M2 Ultra (64GB+ RAM):**
- ✅ `qwen2.5:32b` - Excellent quality
- ✅ `llama3.1:70b` (4-bit quantized)
- Performance: ~20-40 tokens/sec (best local option)

### NVIDIA/AMD GPUs (Linux/Windows)

**Minimum (8GB VRAM):**
- Models: `llama3.2:7b`, `gemma2:7b`, `qwen2.5:7b`
- GPUs: RTX 3070, RTX 4060 Ti, AMD RX 6700 XT

**Recommended (16GB VRAM):**
- Models: `llama3.1:13b`, `qwen2.5:14b`
- GPUs: RTX 4070 Ti, RTX 3090, AMD RX 7900 XT

**Ideal (24GB+ VRAM):**
- Models: `qwen2.5:32b`, `llama3.1:70b`
- GPUs: RTX 4090, RTX 6000 Ada

### CPU-only (Not Recommended)
- Possible but 10-100x slower
- Only for testing basic functionality

## Installation

### Option 1: Native Installation (Recommended for Mac)

**Why native?** Better performance, simpler setup, direct Metal access.

```bash
# Install Ollama directly on macOS
brew install ollama

# Start Ollama service
ollama serve

# Test installation
curl http://localhost:11434/api/tags
```

### Option 2: Docker Installation

For Linux/Windows or if you prefer containerization:

```bash
# Using the integrated docker-compose
docker compose -f docker-compose-ollama.yml up -d

# Or manual
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

## Model Selection

### Recommended Models by Hardware

**For 16GB Mac Mini M4:**
```bash
# Best balance (recommended)
ollama pull qwen2.5:7b

# Alternative options
ollama pull gemma2:9b      # Better quality, slower
ollama pull llama3.2:3b   # Faster, lower quality
```

**For 24GB Mac Mini M4:**
```bash
# Excellent quality (recommended)
ollama pull qwen2.5:14b

# Alternative options
ollama pull llama3.1:13b  # Very good quality
ollama pull gemma2:27b   # Larger model, good quality
```

**For High-End GPUs (24GB+ VRAM):**
```bash
# Best quality
ollama pull qwen2.5:32b

# Excellent alternatives
ollama pull llama3.1:70b   # Very large model
```

### Model Comparison

| Model | Size | RAM/VRAM | Quality | Speed | Best For |
|-------|------|----------|---------|-------|----------|
| qwen2.5:32b | 32B | 24GB+ | Excellent | Medium | Best local option |
| qwen2.5:14b | 14B | 16GB | Very Good | Fast | Balanced choice |
| llama3.1:13b | 13B | 16GB | Good | Fast | Proven model |
| qwen2.5:7b | 7B | 8GB | Good | Very Fast | Budget option |
| gemma2:9b | 9B | 12GB | Good | Fast | Google model |
| llama3.2:3b | 3B | 4GB | Fair | Fastest | Minimum viable |

## Testing Models

Before configuring Sure, test your model:

```bash
# Test transaction categorization
ollama run qwen2.5:7b

# Try these prompts:
# "Categorize this transaction: 'WHOLEFDS LAX 10488' for $52.30"
# "Extract merchant name from: 'SQ *COFFEE SHOP 1234'"
# "What's a good category for 'Netflix Monthly Subscription'?"
```

Expected responses:
- Category: "Groceries", Merchant: "Whole Foods"
- Merchant: "Coffee Shop"
- Category: "Entertainment: Streaming"

## Configure Sure

### Step 1: Edit Environment

Edit `sure/.env`:

```bash
# Add these lines for local AI
SURE_OPENAI_ACCESS_TOKEN=ollama-local
SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1  # Mac
SURE_OPENAI_MODEL=qwen2.5:7b
SURE_AI_DEBUG_MODE=false
```

**For Docker setup (not Mac):**
```bash
SURE_OPENAI_URI_BASE=http://sure-ollama:11434/v1
```

### Step 2: Restart Sure

```bash
docker compose restart sure-web sure-worker
```

### Step 3: Enable AI Features

1. Open Sure in browser
2. Go to Settings → Self-Hosting → AI Provider
3. Agree to enable AI features
4. Test with: "What are my spending categories?"

## Performance Optimization

### Mac-Specific Optimizations

```bash
# Ensure Ollama has enough memory
sudo sysctl -w vm.max_map_count=262144

# Optimize for Metal performance
export METAL_DEVICE_WRAPPER_TYPE=1
```

### Model Tuning

**If responses are too slow:**
```bash
# Switch to smaller model
ollama pull llama3.2:3b
# Update .env: SURE_OPENAI_MODEL=llama3.2:3b
```

**If quality is too low:**
```bash
# Switch to larger model (if you have RAM)
ollama pull qwen2.5:14b
# Update .env: SURE_OPENAI_MODEL=qwen2.5:14b
```

### Batch Processing

For better performance with transaction categorization:
- Process transactions in batches (25-50 at a time)
- Enable auto-categorization for recurring patterns
- Create rules for known transactions

## Docker Integration

Add Ollama service to your `docker-compose.yml`:

```yaml
services:
  sure-web:
    environment:
      SURE_OPENAI_ACCESS_TOKEN: ollama-local
      SURE_OPENAI_URI_BASE: http://sure-ollama:11434/v1
      SURE_OPENAI_MODEL: qwen2.5:7b
    depends_on:
      - sure-ollama

  sure-worker:
    environment:
      SURE_OPENAI_ACCESS_TOKEN: ollama-local
      SURE_OPENAI_URI_BASE: http://sure-ollama:11434/v1
      SURE_OPENAI_MODEL: qwen2.5:7b
    depends_on:
      - sure-ollama

  sure-ollama:
    image: ollama/ollama:latest
    container_name: sure-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ${SURE_DATA_DIR}/ollama:/root/.ollama
    # Uncomment for NVIDIA GPU support
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
    networks:
      - sure

  # Optional: Web UI for model management
  sure-ollama-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: sure-ollama-webui
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ${SURE_DATA_DIR}/ollama-webui:/app/backend/data
    environment:
      OLLAMA_BASE_URL: http://sure-ollama:11434
    depends_on:
      - sure-ollama
    networks:
      - sure
```

## Monitoring

### Check Model Status

```bash
# List installed models
ollama list

# Check model details
ollama show qwen2.5:7b

# Test API connectivity
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Test connection",
  "stream": false
}'
```

### Monitor Resource Usage

```bash
# Check memory usage (Mac)
top -o mem

# Check GPU usage (NVIDIA)
nvidia-smi

# Monitor Ollama logs
docker logs -f sure-ollama
```

## Troubleshooting

### Common Issues

**Problem: Sure can't connect to Ollama**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# For Mac Docker, use correct URL
SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1
# NOT http://localhost:11434/v1
```

**Problem: Out of memory errors**
```bash
# Check available memory
free -h  # Linux
vm_stat | perl -ne '/page size/ && $size=$4; /Pages free/ && printf "%.2f GB\n", $4*$size/1048576/1024'  # Mac

# Switch to smaller model
ollama pull llama3.2:3b
# Update .env
```

**Problem: Responses too slow**
```bash
# Check CPU/Metal usage
Activity Monitor (Mac)
htop (Linux)

# Try smaller or faster model
ollama pull gemma2:9b  # Often faster than qwen2.5
```

**Problem: AI categorization quality poor**
```bash
# Test model directly
ollama run qwen2.5:7b
# Try: "Categorize: 'WHOLEFDS LAX 10488' for $52.30"

# If poor, upgrade model
ollama pull qwen2.5:14b
```

### Model Management

```bash
# Remove unused models
ollama rm llama3.2:3b

# Update to latest version
ollama pull qwen2.5:7b --verbose

# Check model size before pulling
curl http://localhost:11434/api/tags
```

## Cost Analysis

### Local AI vs Cloud AI

**Local AI (Ollama):**
- Hardware cost: $0 (using existing Mac)
- Electricity: ~$5-15/month (24/7 operation)
- Monthly total: ~$5-15

**Cloud AI (Comparison):**
- Deepseek: $2-5/month + your Pro subscription
- Claude API: $10-25/month + your Pro subscription  
- Gemini API: $3-10/month + your Pro subscription

**Break-even:** Ollama pays for itself in 2-6 months vs cloud AI.

### Hardware Investment (if needed)

**For dedicated AI server:**
- RTX 4070 Ti: ~$800-1200
- Used RTX 3090: ~$600-800
- Complete server build: ~$1500-2500

**Payback period:** 1-2 years vs cloud AI costs.

## Next Steps

### Quick Start (5 minutes)

```bash
# 1. Install Ollama
brew install ollama

# 2. Start service
ollama serve

# 3. Pull model (16GB Mac Mini)
ollama pull qwen2.5:7b

# 4. Configure Sure (.env)
SURE_OPENAI_ACCESS_TOKEN=ollama-local
SURE_OPENAI_URI_BASE=http://host.docker.internal:11434/v1
SURE_OPENAI_MODEL=qwen2.5:7b

# 5. Restart Sure
docker compose restart sure-web sure-worker
```

### Advanced Setup

1. **Multiple models** for different tasks
2. **Automated model updates** 
3. **Performance monitoring**
4. **Backup model configurations**

## References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Ollama Model Library](https://ollama.ai/library)
- [Sure AI Integration Guide](ai-integration.md)
- [Apple Metal Performance](https://developer.apple.com/metal/)
- [Docker Compose Integration](../docker-compose-ollama.yml)