# Architecture & Implementation Details

## Overview

This document explains how the OpenClaw agents work internally, including prompts, tool calling, and Ollama API interaction.

## 📦 Three Versions

1. **coding_agent.py** - Simple text-only Q&A (no tools)
2. **openclaw.py** - Full agent with 6 tools (file ops, commands, Python REPL)
3. **openclaw_pro.py** - Advanced agent with 9 tools (adds web browsing, Discord, business planning)

## System Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  coding_agent.py            │
│  (Python CLI)               │
│                             │
│  ┌───────────────────────┐  │
│  │ OllamaCodingAgent     │  │
│  │                       │  │
│  │ - chat()             │  │
│  │ - analyze_code()     │  │
│  │ - interactive_mode() │  │
│  └───────────────────────┘  │
└─────────────┬───────────────┘
              │ HTTP/JSON
              ▼
┌─────────────────────────────┐
│  Ollama API                 │
│  (localhost:11434)          │
│                             │
│  Endpoints:                 │
│  - /api/chat (streaming)    │
│  - /api/tags (list models)  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Local LLM Models           │
│  (CodeLlama, DeepSeek, etc) │
└─────────────────────────────┘
```

## System Prompt

The core system prompt that defines the agent's behavior:

```python
def get_coding_system_prompt(self) -> str:
    """Get the system prompt for coding tasks"""
    return """You are an expert coding assistant. You help developers with:
- Code explanation and understanding
- Bug detection and debugging
- Code review and best practices
- Performance optimization
- Refactoring suggestions
- Writing clean, maintainable code

Provide clear, concise, and actionable advice. Use examples when helpful.
Focus on practical solutions that improve code quality."""
```

### Why This Prompt Works

1. **Role Definition**: "You are an expert coding assistant" - Sets clear identity
2. **Specific Capabilities**: Bullet list defines exactly what the agent does
3. **Output Guidance**: "Clear, concise, actionable" - Guides response format
4. **Practical Focus**: Emphasizes real-world solutions over theory

## Task-Specific Prompts

For file/code analysis, the agent uses task-specific prompt prefixes:

```python
tasks = {
    "explain": "Explain what this code does in detail:",
    "review": "Review this code for bugs, improvements, and best practices:",
    "optimize": "Suggest optimizations for this code:",
    "debug": "Help debug this code and identify potential issues:",
    "refactor": "Suggest refactoring improvements for this code:"
}
```

### Full Prompt Structure

When analyzing code, the complete prompt looks like:

```
SYSTEM MESSAGE:
You are an expert coding assistant. You help developers with:
- Code explanation and understanding
- Bug detection and debugging
[... rest of system prompt ...]

USER MESSAGE:
Review this code for bugs, improvements, and best practices:

```
[code here]
```
```

## API Communication

### How It Works (No Tool Calling)

**Important**: This agent does **NOT** use function/tool calling. It uses **pure text completion** with Ollama's chat API.

### Ollama Chat API

The agent communicates with Ollama using the `/api/chat` endpoint:

```python
def chat(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = True) -> str:
    # Build messages array
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Add conversation history
    messages.extend(self.conversation_history)

    # Add current prompt
    messages.append({"role": "user", "content": prompt})

    # API request payload
    payload = {
        "model": self.model,           # e.g., "codellama"
        "messages": messages,          # Chat history
        "stream": stream               # Enable streaming
    }

    # POST to Ollama
    response = requests.post(
        f"{self.base_url}/api/chat",
        json=payload,
        stream=stream,
        timeout=300
    )
```

### API Request Example

```json
{
  "model": "codellama",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert coding assistant..."
    },
    {
      "role": "user",
      "content": "Explain what this code does:\n\n```python\ndef factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)\n```"
    }
  ],
  "stream": true
}
```

### Streaming Response

The agent uses **streaming** for real-time output:

```python
if stream:
    full_response = ""
    print("Assistant: ", end="", flush=True)

    # Process each chunk as it arrives
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            if 'message' in chunk:
                content = chunk['message'].get('content', '')
                print(content, end="", flush=True)  # Real-time printing
                full_response += content
            if chunk.get('done', False):
                print()  # New line at end
                break
```

### Response Format (from Ollama)

Each streamed chunk looks like:

```json
{
  "model": "codellama",
  "created_at": "2026-05-01T10:00:00Z",
  "message": {
    "role": "assistant",
    "content": "This function "
  },
  "done": false
}
```

Final chunk:

```json
{
  "model": "codellama",
  "created_at": "2026-05-01T10:00:01Z",
  "message": {
    "role": "assistant",
    "content": ""
  },
  "done": true,
  "total_duration": 1234567890,
  "load_duration": 12345678,
  "prompt_eval_count": 42,
  "eval_count": 128
}
```

## Conversation History

The agent maintains conversation context:

```python
self.conversation_history: List[Dict[str, str]] = []

# After each exchange, append to history:
self.conversation_history.append({"role": "user", "content": prompt})
self.conversation_history.append({"role": "assistant", "content": full_response})
```

This allows multi-turn conversations where the model remembers context.

## Key Design Decisions

### 1. Why No Tool Calling?

**Reason**: Simplicity and compatibility.

- **Pro**: Works with any Ollama model (no special function-calling support needed)
- **Pro**: Simpler implementation (no JSON schema parsing)
- **Pro**: Faster responses (no tool execution overhead)
- **Con**: Cannot execute code or interact with external systems
- **Trade-off**: Perfect for this use case (code advice, not code execution)

### 2. Why Streaming?

**Reason**: Better user experience.

```python
stream: bool = True  # Always enabled by default
```

- Shows progress in real-time
- User sees output immediately
- Feels more responsive than waiting for full completion

### 3. Why HTTP Requests vs Ollama Python Library?

**Reason**: Minimal dependencies.

```python
import requests  # Only dependency needed
```

- No heavy SDKs required
- Single dependency (`requests`)
- Easy to understand and modify
- Full control over API interaction

## Comparison: This Agent vs Claude

| Feature | This Agent | Claude (like me) |
|---------|-----------|------------------|
| **Architecture** | HTTP → Local LLM | API → Cloud LLM |
| **Tool Calling** | ❌ No tools | ✅ 20+ tools (Read, Write, Bash, etc.) |
| **Prompt Style** | System + User | System + User + Tools |
| **Context** | Conversation history | Full conversation + tool results |
| **Capabilities** | Text advice only | Code execution, file ops, git, testing |
| **Response** | Streaming text | Text + tool calls |

### Example Comparison

**This Agent**:
```
User: Review this code
Agent: [Streams text response with review]
```

**Claude (me)**:
```
User: Review this code
Claude: [Calls Read tool to read file]
        [Analyzes code]
        [Returns review with specific line numbers]
        [Can call Edit tool to fix issues]
```

## Prompt Engineering Tips

### Making the Agent Better

You can improve the agent by modifying `get_coding_system_prompt()`:

#### Example 1: Add Specific Language Expertise
```python
return """You are an expert Python coding assistant specializing in:
- Django and Flask web frameworks
- pandas and numpy for data science
- pytest for testing
- PEP 8 style guidelines

Focus on Pythonic solutions and modern best practices."""
```

#### Example 2: Add Output Format
```python
return """You are an expert coding assistant.

When reviewing code, ALWAYS use this format:
1. **Summary**: Brief overview
2. **Issues**: List of problems found
3. **Suggestions**: Specific improvements
4. **Example**: Show corrected code

Be specific and cite line numbers when possible."""
```

#### Example 3: Add Personality
```python
return """You are a friendly, patient coding mentor.

Guidelines:
- Explain concepts clearly for beginners
- Use analogies and examples
- Encourage good practices
- Be supportive and constructive
- Ask clarifying questions when needed"""
```

## Advanced: Adding Tool-Like Behavior

While this agent doesn't use formal tool calling, you can simulate tool-like behavior with **prompt engineering**:

### Example: Structured Output

```python
def analyze_code_structured(self, code: str) -> Dict[str, any]:
    prompt = f"""Analyze this code and respond ONLY with valid JSON:

{{
  "language": "detected language",
  "complexity": "low|medium|high",
  "issues": ["list of issues"],
  "suggestions": ["list of suggestions"],
  "score": 0-100
}}

Code:
```
{code}
```"""

    response = self.chat(prompt, system_prompt="You are a code analyzer. Always respond with valid JSON.")

    try:
        return json.loads(response)
    except:
        return {"error": "Failed to parse response"}
```

This gives you structured data without formal tool calling!

## Performance Characteristics

### Speed Factors

1. **Model Size**:
   - 3B models: ~2-5 seconds
   - 7B models: ~5-10 seconds
   - 13B+ models: ~10-30 seconds

2. **Streaming**:
   - First token: 1-3 seconds
   - Subsequent: Real-time

3. **Context Length**:
   - More history = slower processing
   - Use `/clear` to reset context

### Resource Usage

```
Model Size → RAM Usage
3B        → 4-6 GB
7B        → 8-10 GB
13B       → 16-20 GB
33B       → 32-40 GB
```

## Security Considerations

### What's Safe

✅ All computation is local
✅ No data sent to cloud
✅ No telemetry or tracking
✅ Code never leaves your machine

### What to Watch

⚠️ Model responses are non-deterministic
⚠️ Always review suggested code changes
⚠️ Don't blindly execute generated code
⚠️ Models can hallucinate or be wrong

## Extension Ideas

### Adding Features Without Tool Calling

1. **Pre-process Input**: Parse code with AST before sending to LLM
2. **Post-process Output**: Extract JSON from text responses
3. **Context Enhancement**: Include relevant docs/examples in prompt
4. **Multi-step Reasoning**: Chain multiple prompts together
5. **Validation**: Check responses against linters/formatters

### Example: Multi-step Analysis

```python
def deep_review(self, code: str) -> str:
    # Step 1: Get high-level summary
    summary = self.chat(f"Briefly summarize this code:\n```\n{code}\n```")

    # Step 2: Find security issues
    security = self.chat(f"Find security issues in this code:\n```\n{code}\n```")

    # Step 3: Performance analysis
    performance = self.chat(f"Analyze performance of:\n```\n{code}\n```")

    # Combine results
    return f"Summary:\n{summary}\n\nSecurity:\n{security}\n\nPerformance:\n{performance}"
```

## Summary

### Core Architecture
- **Simple**: HTTP requests to local Ollama API
- **Fast**: Streaming responses for real-time feedback
- **Lightweight**: Single dependency (requests)
- **Private**: Everything runs locally

### Key Techniques
- **System Prompts**: Define agent behavior and expertise
- **Task Prompts**: Specific instructions for different analysis types
- **Conversation History**: Multi-turn context management
- **Streaming**: Real-time output for better UX

### No Tool Calling Required
- Uses pure text completion
- Simpler than function-calling approaches
- Perfect for advice/analysis use cases
- Can simulate structured output with prompt engineering

This design prioritizes **simplicity**, **speed**, and **privacy** over advanced capabilities like code execution or file manipulation.
