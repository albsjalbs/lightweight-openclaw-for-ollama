# Lightweight OpenClaw for Ollama

A fast, lightweight coding assistant powered by local Ollama models - a lightweight alternative to Claude for coding tasks.

## Features

- 🚀 **Fast & Local**: Runs entirely on your machine using Ollama
- 💬 **Interactive Chat**: Conversational interface for coding questions
- 📁 **File Analysis**: Analyze code files directly
- 🔍 **Multiple Tasks**: Code review, debugging, optimization, refactoring
- 🎯 **Focused**: Specialized for coding tasks
- 🔒 **Private**: All data stays on your machine

## Prerequisites

1. **Install Ollama**: [https://ollama.ai](https://ollama.ai)
2. **Pull a coding model**:
   ```bash
   # Recommended: CodeLlama (7B - fast)
   ollama pull codellama

   # Or DeepSeek Coder (6.7B - excellent for code)
   ollama pull deepseek-coder

   # Or Qwen Coder (smaller, faster)
   ollama pull qwen2.5-coder
   ```

3. **Start Ollama service**:
   ```bash
   ollama serve
   ```

## Installation

```bash
# Clone or download this repository
cd lightweight-openclaw-for-ollama

# Install dependencies
pip install -r requirements.txt

# Make executable (optional)
chmod +x coding_agent.py
```

## Usage

### Interactive Mode (Default)

```bash
python coding_agent.py
```

Interactive commands:
- `/help` - Show help
- `/clear` - Clear conversation history
- `/models` - List available models
- `/exit` - Exit

### Analyze a Code File

```bash
# Explain what the code does
python coding_agent.py --file script.py --task explain

# Review code for issues
python coding_agent.py --file app.py --task review

# Suggest optimizations
python coding_agent.py --file algo.py --task optimize

# Debug assistance
python coding_agent.py --file buggy.py --task debug

# Refactoring suggestions
python coding_agent.py --file legacy.py --task refactor
```

### One-Shot Questions

```bash
python coding_agent.py --prompt "How do I reverse a string in Python?"
python coding_agent.py --prompt "Explain async/await in JavaScript"
```

### Use Different Models

```bash
# Use DeepSeek Coder
python coding_agent.py --model deepseek-coder

# Use Qwen Coder
python coding_agent.py --model qwen2.5-coder

# List available models
python coding_agent.py --list-models
```

## Recommended Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `codellama` | 7B | Fast | Good | General coding |
| `deepseek-coder` | 6.7B | Fast | Excellent | Code generation |
| `qwen2.5-coder` | 3B | Very Fast | Good | Quick tasks |
| `codellama:13b` | 13B | Medium | Better | Complex problems |
| `deepseek-coder:33b` | 33B | Slow | Best | Production code |

## Examples

### Example 1: Interactive Coding Help
```bash
$ python coding_agent.py

🤖 Lightweight Coding Assistant (Ollama)
📦 Model: codellama
💡 Commands: /help, /clear, /models, /exit
------------------------------------------------------------

You: How do I read a CSV file in Python?
Assistant: Here's how to read a CSV file in Python using the built-in csv module...

You: What about using pandas?
Assistant: With pandas, it's even simpler...
```

### Example 2: Code Review
```bash
$ python coding_agent.py --file my_script.py --task review

📁 Analyzing: my_script.py
📊 Task: review
------------------------------------------------------------
Assistant: Here's my review of your code:

1. **Potential Issues:**
   - Line 15: Possible IndexError...

2. **Improvements:**
   - Consider using a with statement...
```

### Example 3: Quick Question
```bash
$ python coding_agent.py --prompt "What's the difference between == and === in JavaScript?"
```

## Comparison: OpenClaw vs Claude

| Feature | OpenClaw | Claude |
|---------|----------|--------|
| Speed | ⚡ Very Fast (local) | Medium (API) |
| Privacy | 🔒 100% Local | Cloud-based |
| Cost | 💰 Free | Paid API |
| Context | Limited (model size) | Large context |
| Complexity | Simple tasks | Complex tasks |
| Best Use | Quick help, reviews | Architecture, planning |

## Tips for Best Results

1. **Choose the right model**: Smaller models (3B-7B) for speed, larger (13B-33B) for quality
2. **Be specific**: Clear questions get better answers
3. **Provide context**: Include relevant code snippets
4. **Iterate**: Use interactive mode for back-and-forth discussion
5. **Combine tools**: Use this for quick tasks, Claude for complex problems

## Troubleshooting

### "Ollama service not running"
```bash
# Start Ollama
ollama serve
```

### "No models found"
```bash
# Install a model
ollama pull codellama
```

### Slow responses
- Use smaller models (qwen2.5-coder:3b)
- Close other applications
- Check CPU/RAM usage

### Connection refused
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Try different port
python coding_agent.py --base-url http://localhost:11435
```

## Advanced Usage

### Custom System Prompts
Edit `coding_agent.py` and modify the `get_coding_system_prompt()` method to customize the agent's behavior.

### Integration with Editors
Add as a custom command in VS Code, Vim, or your preferred editor.

### Batch Processing
Process multiple files:
```bash
for file in *.py; do
    python coding_agent.py --file "$file" --task review > "reviews/${file%.py}_review.txt"
done
```

## Contributing

Feel free to enhance this tool:
- Add more task types
- Improve prompts
- Add editor integrations
- Support more languages

## License

MIT License - Use freely!

---

**Created**: 2026-05-01
**Purpose**: Lightweight local coding assistant using Ollama - A lightweight OpenClaw alternative
