# Sure Documentation

Welcome to the Sure finance app documentation! This directory contains comprehensive guides to help you understand and get the most out of Sure.

## Quick Links

### Getting Started
- [Main README](../README.md) - Installation and setup
- [How Sure Works](how-it-works.md) - Architecture and core features
- **[Ollama Setup Guide](ollama-setup.md)** - Complete local AI setup guide ⭐

### Using Sure
- [Expense Analysis & Spending Insights](expense-analysis.md) - Get insights from your spending data
- [AI Integration & Transaction Categorization](ai-integration.md) - Setup and use AI features

## Documentation Overview

### 📖 [How Sure Works](how-it-works.md)

**What you'll learn:**
- Overall architecture and how components work together
- Core features: accounts, transactions, budgets, categories
- Rules engine for automation
- Reporting and insights capabilities
- Security and privacy features
- Comparison to other finance apps

**Who should read this:**
- New users wanting to understand what Sure can do
- Users migrating from other finance apps
- Anyone curious about the technical architecture

**Time to read:** 20-30 minutes

---

### 📊 [Expense Analysis & Spending Insights](expense-analysis.md)

**What you'll learn:**
- How to analyze spending patterns and trends
- Advanced analysis techniques (category, merchant, time-based)
- Using the AI assistant for financial insights
- Budget vs. actual analysis
- Benchmarking your spending against averages
- Actionable weekly, monthly, and quarterly review processes

**Who should read this:**
- Users who want to understand their spending habits
- Anyone trying to optimize their budget
- Users looking to extract maximum value from their financial data

**Time to read:** 30-40 minutes

---

### 🤖 [AI Integration & Transaction Categorization](ai-integration.md)

**What you'll learn:**
- How to set up AI features (cloud or local)
- Automatic transaction categorization
- Merchant name enhancement
- AI chat assistant for financial queries
- Cloud provider options (OpenAI, Google Gemini, Anthropic Claude)
- Local AI with Ollama for privacy
- Cost optimization strategies
- Privacy and security considerations

**Who should read this:**
- Users who want to automate transaction categorization
- Anyone interested in the AI chat assistant
- Privacy-focused users considering local AI
- Users trying to minimize AI costs

**Time to read:** 45-60 minutes

---

## Common Questions

### "I just installed Sure. Where do I start?"

1. Read the [Main README](../README.md) for installation
2. Skim [How Sure Works](how-it-works.md) to understand the basics (focus on "Core Features")
3. Set up your accounts and import transactions
4. Optionally: Set up [AI Integration](ai-integration.md) for auto-categorization
5. Use [Expense Analysis](expense-analysis.md) as a reference when you're ready to analyze spending

### "How do I get Sure to automatically categorize transactions?"

See the [AI Integration guide](ai-integration.md):
- **Quick Start** section for cloud AI (OpenAI)
- **Local AI with Ollama** section for privacy-focused setup
- **Automatic Transaction Categorization** section for configuration

### "How can I understand my spending habits better?"

The [Expense Analysis guide](expense-analysis.md) covers:
- **Category Analysis** - Where your money goes
- **Merchant Analysis** - Who you spend with
- **Time-Based Analysis** - Trends over time
- **Budget vs. Actual** - Tracking against goals
- **AI Assistant** - Ask questions in natural language

### "Is my data private with AI features?"

See [AI Integration - Privacy & Security](ai-integration.md#privacy--security-considerations):
- **Cloud AI**: Data sent to provider (OpenAI, Google, etc.)
- **Local AI (Ollama)**: Data never leaves your server
- **What's sent**: Transaction details, questions (not passwords, account numbers)

### "How much does the AI cost?"

See [AI Integration - Cost Optimization](ai-integration.md#cost-optimization):
- **Typical monthly costs**: $5-20 for cloud AI
- **Free option**: Local AI with Ollama (electricity + hardware only)
- **Hybrid approach**: Mix cloud and local for best balance

### "Can I use Sure offline?"

**Partially:**
- ✅ Basic features work offline (accounts, transactions, budgets, reports)
- ✅ AI chat works offline if using local Ollama
- ❌ Bank syncing requires internet (uses Plaid API)
- ❌ Cloud AI requires internet

## Feature Roadmap

Sure is actively developed. Check the [GitHub repository](https://github.com/we-promise/sure) for:
- Latest releases and changelogs
- Upcoming features
- Known issues
- Community discussions

## Contributing

Found an error in the docs or have a suggestion?
1. Open an issue at [Sure GitHub Issues](https://github.com/we-promise/sure/issues)
2. Submit a pull request with improvements
3. Join discussions in [GitHub Discussions](https://github.com/we-promise/sure/discussions)

## External Resources

### Official Sure Resources
- [Sure Website](https://sure.am/)
- [GitHub Repository](https://github.com/we-promise/sure)
- [Release Notes](https://github.com/we-promise/sure/releases)
- [GitHub Discussions](https://github.com/we-promise/sure/discussions)

### Related Projects
- [Maybe Finance (original project)](https://github.com/maybe-finance/maybe)
- [Actual Budget](https://actualbudget.com/) - Alternative self-hosted finance app
- [Plaid](https://plaid.com/) - Bank connection API used by Sure

### Learning Resources
- [Personal Finance Basics](https://www.investopedia.com/personal-finance-4427760)
- [50/30/20 Budgeting Rule](https://www.investopedia.com/ask/answers/022916/what-502030-budget-rule.asp)
- [Consumer Expenditure Survey](https://www.bls.gov/cex/) - US spending benchmarks

## Documentation Updates

These docs are maintained alongside Sure deployment in the Focus repository.

**Last Updated:** January 2026

**Sure Version:** v0.6.6+

**Docs Version:** 1.0

---

## Quick Reference Card

### Key AI Chat Queries

**Spending Overview:**
```
"How much did I spend last month?"
"What are my top 5 spending categories?"
```

**Budget Tracking:**
```
"Which budget categories am I over this month?"
"Am I on track with my grocery budget?"
```

**Trends:**
```
"Compare my spending this month vs last month"
"Show me my spending trends for the last 6 months"
```

**Specific Analysis:**
```
"How much do I spend on average per month on restaurants?"
"What unusual transactions happened this week?"
```

### Common Tasks

| Task | Where to Go |
|------|-------------|
| Install Sure | [Main README](../README.md) |
| Set up AI | [AI Integration - Quick Start](ai-integration.md#quick-start) |
| Analyze spending | [Expense Analysis](expense-analysis.md) |
| Create budgets | [How Sure Works - Budgeting](how-it-works.md#3-budgeting-system) |
| Set up rules | [How Sure Works - Rules Engine](how-it-works.md#5-rules-engine) |
| Export data | [Expense Analysis - Exporting Data](expense-analysis.md#exporting-data-for-external-analysis) |

---

**Need help?** Check [GitHub Discussions](https://github.com/we-promise/sure/discussions) or open an [issue](https://github.com/we-promise/sure/issues).
