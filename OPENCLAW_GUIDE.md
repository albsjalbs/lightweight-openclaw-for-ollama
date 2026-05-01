# OpenClaw Guide - Full-Featured Agent with Tool Calling

## What is OpenClaw?

OpenClaw is a **full-featured coding agent** that runs locally using Ollama. Unlike simple chatbots, OpenClaw can:

- 📖 Read and analyze files automatically
- ✍️ Write and modify code files
- ⚙️ Execute shell commands
- 🐍 Run Python code
- 🔍 Search your codebase
- 🤖 Use tools autonomously like Claude

## Quick Start

```bash
# 1. Install model with tool-calling support
ollama pull qwen2.5-coder:7b

# 2. Start Ollama (if not running)
ollama serve

# 3. Run OpenClaw
python openclaw.py
```

## How It Works

### Agentic Workflow

```
User: "Review app.py"
    ↓
OpenClaw thinks: "I need to read the file first"
    ↓
Executes: read_file(app.py)
    ↓
Analyzes the code
    ↓
Responds: "I found 3 issues in app.py..."
```

### Tool Calling System

OpenClaw uses **structured tool calling**. The model outputs JSON to request tool use:

```python
# Model output:
"I'll read the file now."
{"tool": "read_file", "parameters": {"file_path": "app.py"}}

# OpenClaw executes the tool and sends results back
# Model continues with the file contents
```

## Available Tools

### 1. `read_file` - Read File Contents
```python
{"tool": "read_file", "parameters": {"file_path": "app.py"}}
```

**Use cases**:
- Code review
- Understanding existing code
- Finding bugs
- Analysis

### 2. `write_file` - Write/Create Files
```python
{"tool": "write_file", "parameters": {
    "file_path": "new_script.py",
    "content": "print('Hello, World!')"
}}
```

**Use cases**:
- Creating new files
- Fixing bugs
- Refactoring
- Implementing features

### 3. `list_directory` - List Directory Contents
```python
{"tool": "list_directory", "parameters": {"path": "src/"}}
```

**Use cases**:
- Understanding project structure
- Finding files
- Exploring codebases

### 4. `run_command` - Execute Shell Commands
```python
{"tool": "run_command", "parameters": {
    "command": "pytest tests/",
    "working_dir": "."
}}
```

**Use cases**:
- Running tests
- Building projects
- Git operations
- Package management

### 5. `search_files` - Search Text in Files
```python
{"tool": "search_files", "parameters": {
    "pattern": "TODO",
    "path": ".",
    "file_pattern": "*.py"
}}
```

**Use cases**:
- Finding TODOs
- Searching for functions
- Code archaeology
- Refactoring prep

### 6. `python_repl` - Execute Python Code
```python
{"tool": "python_repl", "parameters": {
    "code": "import sys\nprint(sys.version)"
}}
```

**Use cases**:
- Testing code snippets
- Quick calculations
- Validating logic
- Prototyping

## Usage Examples

### Example 1: Code Review

```
👤 You: Review app.py and suggest improvements

🦅 OpenClaw: I'll read app.py first.
🔧 Executing: read_file({"file_path": "app.py"})
✅ Result: File: app.py...

🦅 OpenClaw: I've reviewed app.py. Here are my findings:

1. **Bug on line 15**: Missing null check before accessing user.email
2. **Performance issue line 23**: Using O(n²) algorithm, can optimize to O(n)
3. **Security concern line 45**: SQL query vulnerable to injection

Would you like me to fix these issues?
```

### Example 2: Create New Feature

```
👤 You: Create a Python script that reads CSV and generates a report

🦅 OpenClaw: I'll create a CSV report generator for you.
🔧 Executing: write_file({
    "file_path": "csv_reporter.py",
    "content": "import csv\nimport sys..."
})
✅ Result: Successfully wrote to csv_reporter.py

🦅 OpenClaw: I've created csv_reporter.py with the following features:
- Reads CSV files
- Generates summary statistics
- Exports formatted reports
- Handles errors gracefully

Would you like me to test it?
```

### Example 3: Debug and Fix

```
👤 You: My tests are failing. Debug and fix the issue.

🦅 OpenClaw: Let me run the tests first.
🔧 Executing: run_command({"command": "pytest tests/ -v"})
✅ Result: FAILED tests/test_auth.py::test_login

🦅 OpenClaw: I'll read the failing test.
🔧 Executing: read_file({"file_path": "tests/test_auth.py"})

🦅 OpenClaw: Found the issue. The test expects status code 200,
but the code returns 201 for successful login.

🔧 Executing: read_file({"file_path": "auth.py"})

🦅 OpenClaw: I'll fix the auth.py to return 200.
🔧 Executing: write_file({"file_path": "auth.py", ...})

🦅 OpenClaw: Fixed! Run pytest again to verify.
```

### Example 4: Refactoring

```
👤 You: Refactor the authentication module to use async/await

🦅 OpenClaw: I'll start by listing the files in the auth module.
🔧 Executing: list_directory({"path": "auth/"})

🦅 OpenClaw: I found 3 files to refactor. I'll update each:

🔧 Executing: read_file({"file_path": "auth/login.py"})
🔧 Executing: write_file({"file_path": "auth/login.py", ...})

🔧 Executing: read_file({"file_path": "auth/signup.py"})
🔧 Executing: write_file({"file_path": "auth/signup.py", ...})

🔧 Executing: read_file({"file_path": "auth/logout.py"})
🔧 Executing: write_file({"file_path": "auth/logout.py", ...})

🦅 OpenClaw: Refactoring complete! All auth functions now use async/await.
Would you like me to update the tests?
```

## Command Line Options

### Interactive Mode (Default)
```bash
python openclaw.py
```

Starts a chat session where you can have multi-turn conversations.

### One-Shot Task
```bash
python openclaw.py --task "Create a FastAPI app with user authentication"
```

Executes a single task and exits.

### Custom Model
```bash
python openclaw.py --model qwen2.5-coder:32b
```

Uses a different Ollama model.

### Custom Ollama URL
```bash
python openclaw.py --base-url http://192.168.1.100:11434
```

Connects to Ollama on a different machine.

## Interactive Commands

While in interactive mode:

- `/help` - Show help message
- `/clear` - Clear conversation history
- `/tools` - List available tools
- `/exit` - Exit OpenClaw

## Recommended Models

### Best Models for OpenClaw

OpenClaw works best with models that support **tool calling** and **structured output**:

| Model | Size | Speed | Quality | Tool Support |
|-------|------|-------|---------|--------------|
| `qwen2.5-coder:7b` | 7B | Fast | Good | ✅ Excellent |
| `qwen2.5-coder:32b` | 32B | Slow | Best | ✅ Excellent |
| `deepseek-coder-v2:16b` | 16B | Medium | Excellent | ✅ Good |
| `codellama:13b` | 13B | Medium | Good | ⚠️ Limited |

**Recommended**: `qwen2.5-coder:7b` - Best balance of speed and quality

### Why These Models?

These models are trained to:
- Output structured JSON
- Follow tool schemas
- Reason about when to use tools
- Chain multiple tool calls

## Tips for Best Results

### 1. Be Specific
```
❌ "Fix the bug"
✅ "Debug why app.py is failing and fix the authentication bug"
```

### 2. Let It Use Tools
```
✅ "Review and fix all Python files in src/"
   → OpenClaw will automatically read each file
```

### 3. Multi-Step Tasks Work Great
```
✅ "Create a Flask API, write tests, and run them"
   → OpenClaw will:
   1. Create the API files
   2. Create test files
   3. Run pytest
   4. Fix any issues
```

### 4. Iterative Development
```
You: "Create a user authentication system"
OpenClaw: [Creates files]

You: "Add password reset functionality"
OpenClaw: [Reads existing code, adds feature]

You: "Now add rate limiting"
OpenClaw: [Updates code with rate limiting]
```

## Advanced Usage

### Custom System Prompt

Edit `openclaw.py` and modify the `get_system_prompt()` method to customize behavior:

```python
def get_system_prompt(self) -> str:
    return """You are OpenClaw, a senior software engineer.

    Your style:
    - Write clean, well-documented code
    - Follow PEP 8 for Python
    - Add type hints
    - Write comprehensive tests

    Always explain your reasoning before using tools."""
```

### Adding New Tools

Create a new tool class:

```python
class GitStatusTool(Tool):
    def __init__(self):
        super().__init__(
            name="git_status",
            description="Get git repository status",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        )

    def execute(self) -> str:
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True
        )
        return result.stdout
```

Register it in `OpenClawAgent.__init__`:

```python
self.tools["git_status"] = GitStatusTool()
```

## Troubleshooting

### "Tool not found" error
- Make sure the model outputs valid JSON
- Check that the tool name matches exactly
- Some models struggle with tool calling - use qwen2.5-coder

### Slow responses
- Use smaller models (qwen2.5-coder:7b vs :32b)
- Reduce context with `/clear`
- Check CPU/GPU usage

### Model not following instructions
- Try different models (qwen2.5-coder is best)
- Make requests more specific
- Use one-shot mode with `--task` for single operations

### Tool execution errors
- Check file paths are correct
- Verify you have permissions
- Commands timeout after 30s (configurable)

## Comparison: OpenClaw vs Coding Agent

| Feature | OpenClaw | Coding Agent |
|---------|----------|--------------|
| **File Operations** | ✅ Automatic | ❌ Manual paste |
| **Code Execution** | ✅ Yes | ❌ No |
| **Shell Commands** | ✅ Yes | ❌ No |
| **Tool Calling** | ✅ Yes | ❌ No |
| **Speed** | Medium | Fast |
| **Complexity** | High | Low |
| **Best For** | Real work | Q&A, learning |

## Security Considerations

### What OpenClaw Can Do

⚠️ **OpenClaw has full filesystem access** - It can:
- Read any file you can read
- Write/modify files
- Execute arbitrary commands
- Run Python code

### Safety Tips

1. **Review before approving**: Always review code before running
2. **Use in safe environments**: Test in development, not production
3. **Limit scope**: Don't give it access to sensitive directories
4. **Check commands**: Verify shell commands before execution
5. **Version control**: Use git so you can revert changes

### Safe Usage Pattern

```bash
# Work in a clean git repository
git status  # Make sure it's clean

# Use OpenClaw
python openclaw.py

# Review changes
git diff

# If good, commit
git add .
git commit -m "Changes made by OpenClaw"

# If bad, revert
git reset --hard
```

## Real-World Examples

### Example 1: API Development

```
You: Create a RESTful API for a todo app with FastAPI

OpenClaw will:
1. Create main.py with FastAPI setup
2. Create models.py with Pydantic models
3. Create database.py with SQLite setup
4. Create routes for CRUD operations
5. Create requirements.txt
6. Test the endpoints
```

### Example 2: Testing Suite

```
You: Create comprehensive tests for my authentication module

OpenClaw will:
1. Read the auth module code
2. Identify all functions
3. Create test cases for each
4. Add edge cases
5. Run the tests
6. Fix any failures
```

### Example 3: Code Migration

```
You: Migrate this JavaScript code to TypeScript

OpenClaw will:
1. Read all .js files
2. Convert to TypeScript
3. Add type annotations
4. Create tsconfig.json
5. Run tsc to verify
6. Fix any type errors
```

## Summary

OpenClaw brings **Claude-like capabilities** to your local machine:

✅ **Automated**: Uses tools without asking
✅ **Fast**: Runs on your hardware
✅ **Private**: Code never leaves your machine
✅ **Free**: No API costs
✅ **Powerful**: Full filesystem and command access

**Perfect for**:
- Real coding tasks
- File manipulation
- Running tests
- Building features
- Refactoring
- Automation

Start using OpenClaw today and experience local AI with real coding power! 🦅
