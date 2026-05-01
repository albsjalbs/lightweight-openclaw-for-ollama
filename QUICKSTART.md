# Quick Start Guide

## 1-Minute Setup

```bash
# Run the setup script
./setup.sh

# Or manually:
pip install -r requirements.txt
ollama pull codellama
```

## Common Commands

### Interactive Chat (Recommended for Beginners)
```bash
python coding_agent.py
```

### Quick Code Review
```bash
python coding_agent.py --file yourcode.py --task review
```

### Quick Question
```bash
python coding_agent.py --prompt "Your question here"
```

### Try the Example
```bash
python coding_agent.py --file example_test.py --task optimize
```

## Model Recommendations

**For Speed (Recommended)**:
```bash
ollama pull qwen2.5-coder:3b    # Fastest, good quality
python coding_agent.py --model qwen2.5-coder:3b
```

**For Balance**:
```bash
ollama pull codellama           # Default, 7B, good all-around
python coding_agent.py          # Uses codellama by default
```

**For Quality**:
```bash
ollama pull deepseek-coder:6.7b # Best code understanding
python coding_agent.py --model deepseek-coder:6.7b
```

## Troubleshooting One-Liners

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# List installed models
ollama list

# Pull a model
ollama pull codellama

# Test the agent
python coding_agent.py --prompt "Hello"
```

## Use Cases

### 🐛 Debug Help
```bash
python coding_agent.py --file buggy_code.py --task debug
```

### 📝 Code Explanation
```bash
python coding_agent.py --file complex_code.py --task explain
```

### ⚡ Optimization
```bash
python coding_agent.py --file slow_code.py --task optimize
```

### 🔄 Refactoring
```bash
python coding_agent.py --file legacy_code.py --task refactor
```

### 👀 Code Review
```bash
python coding_agent.py --file new_feature.py --task review
```

## Interactive Commands

When in interactive mode (`python coding_agent.py`):

- `/help` - Show help
- `/clear` - Clear conversation history
- `/models` - List available models
- `/exit` - Exit

## Tips

1. **Start small**: Use smaller models (3B-7B) for quick tasks
2. **Be specific**: "Review this function for memory leaks" beats "Is this good?"
3. **Iterate**: Use interactive mode for back-and-forth discussions
4. **Context matters**: Include relevant code snippets in your questions
5. **Combine tools**: Use this for quick help, Claude for complex architecture

## What Makes This "Lightweight"?

- ⚡ **Fast**: Runs locally, no API delays
- 💰 **Free**: No API costs
- 🔒 **Private**: Your code never leaves your machine
- 🎯 **Focused**: Optimized for coding tasks only
- 📦 **Small**: Uses efficient models (3B-7B typically)

## Next Steps

1. Try the example: `python coding_agent.py --file example_test.py --task optimize`
2. Ask a question: `python coding_agent.py --prompt "How do I...?"`
3. Start interactive chat: `python coding_agent.py`
4. Read full docs: `README.md`

---

**Need Help?** Run `python coding_agent.py --help`
