# AI Agent Framework - Quick Setup Guide

## Your Current Setup

**LLM Server**: GPT-OSS:120b (Reasoning Model)
**Server URL**: http://192.168.1.95:8000/v1
**Framework**: Pre-configured and ready to use!

## Installation

```bash
# Install required dependency
pip install openai

# Verify configuration
python config.py

# Test reasoning extraction
python test_reasoning_extraction.py
```

## What's Special About Your Setup

Your server runs **GPT-OSS:120b**, a reasoning model that outputs its complete chain of thought. The framework automatically handles this:

### Example Output from GPT-OSS:120b:
```
[300+ chars of reasoning and thinking]
<|start|>assistant<|channel|>final<|message|>
The solution is to use approach X because...
```

### What Agents Receive:
```
The solution is to use approach X because...
```

**No code changes needed** - the framework handles extraction transparently!

## Running the Framework

```bash
# Basic usage
python main.py "Create a simple calculator"

# Interactive mode
python main.py
# Then enter your objective when prompted

# Test modes
python main.py
# Choose option 2 for simple test
# Choose option 3 for complexity demo
```

## Configuration Files

All settings in one place: `config.py`

```python
# Provider Settings
LLM_PROVIDER = "openai"                                  # or "ollama"
LLM_MODEL = "llama3.1:8b"
OPENAI_BASE_URL = "http://192.168.1.95:8000/v1"
OPENAI_API_KEY = "not-needed"

# Reasoning Model Settings (for GPT-OSS:120b)
EXTRACT_FINAL_ANSWER = True                             # Enable extraction
FINAL_ANSWER_MARKER = "<|start|>assistant<|channel|>final<|message|>"
```

## How It Works

```
┌─────────────────────────────────────────────────┐
│  Your GPT-OSS:120b Server (Reasoning Model)    │
│  http://192.168.1.95:8000/v1                   │
└───────────────┬─────────────────────────────────┘
                │
                │ [Reasoning + Marker + Final Answer]
                ↓
┌─────────────────────────────────────────────────┐
│  LLMClient (Abstraction Layer)                  │
│  - Detects reasoning marker                     │
│  - Extracts final answer                        │
│  - Cleans up end markers                        │
└───────────────┬─────────────────────────────────┘
                │
                │ [Clean Final Answer Only]
                ↓
┌─────────────────────────────────────────────────┐
│  Agent Framework (Project Planner, Manager,     │
│  Worker, Classifiers, Validators, etc.)         │
│  - Receives clean responses                     │
│  - Works transparently                          │
└─────────────────────────────────────────────────┘
```

## Key Features

✅ **OpenAI-Compatible**: Works with any OpenAI API format
✅ **Reasoning Model Ready**: Automatically extracts final answers
✅ **Configurable**: Easy settings in config.py
✅ **Tested**: Full test suite included
✅ **Zero Code Changes**: All agents work as-is

## Verification Steps

1. **Check Configuration**
   ```bash
   python config.py
   ```
   Should show your server URL and extraction enabled.

2. **Test Extraction**
   ```bash
   python test_reasoning_extraction.py
   ```
   Should show all tests passing.

3. **Test Framework**
   ```bash
   python main.py
   # Choose option 2 for simple test
   ```

## Documentation

- **CLAUDE.md** - Complete framework documentation for Claude Code
- **REASONING_MODELS.md** - Detailed reasoning model documentation
- **MIGRATION_SUMMARY.md** - Migration and refactoring details
- **config.py** - All configuration options

## Customization

### To Disable Extraction (See Full Reasoning)
```python
# In config.py
EXTRACT_FINAL_ANSWER = False
```

### To Change the Marker
```python
# In config.py
FINAL_ANSWER_MARKER = "<your_custom_marker>"
```

### To Switch to Local Ollama
```bash
# Install ollama
pip install ollama

# Update config.py
LLM_PROVIDER = "ollama"
```

## Support

- Report issues: Check framework logs for errors
- Test connectivity: `curl http://192.168.1.95:8000/v1/models`
- Verify extraction: `python test_reasoning_extraction.py`

## Next Steps

1. ✅ Configuration is ready
2. ✅ Reasoning extraction is enabled
3. ✅ Tests are passing
4. ➡️ Run your first project: `python main.py "Your objective"`

---

**Your framework is fully configured for GPT-OSS:120b!**
Everything works transparently - just run it and let the agents handle the complexity.
