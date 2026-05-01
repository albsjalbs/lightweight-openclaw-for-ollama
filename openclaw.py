#!/usr/bin/env python3
"""
OpenClaw for Ollama - Full-featured coding agent with tool calling
Fast, local alternative to Claude with file operations, code execution, and more
"""

import os
import sys
import json
import subprocess
import argparse
import requests
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import re


class Tool:
    """Base class for tools that the agent can use"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to Ollama tool format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def execute(self, **kwargs) -> str:
        """Execute the tool - override in subclasses"""
        raise NotImplementedError


class ReadFileTool(Tool):
    """Tool to read file contents"""

    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        )

    def execute(self, file_path: str) -> str:
        """Read file contents"""
        try:
            path = Path(file_path).expanduser().resolve()
            if not path.exists():
                return f"Error: File '{file_path}' not found"

            content = path.read_text()
            return f"File: {file_path}\n\n{content}"
        except Exception as e:
            return f"Error reading file: {e}"


class WriteFileTool(Tool):
    """Tool to write file contents"""

    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to a file (creates or overwrites)",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        )

    def execute(self, file_path: str, content: str) -> str:
        """Write content to file"""
        try:
            path = Path(file_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return f"Successfully wrote {len(content)} characters to {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"


class ListDirectoryTool(Tool):
    """Tool to list directory contents"""

    def __init__(self):
        super().__init__(
            name="list_directory",
            description="List files and directories in a given path",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (default: current directory)"
                    }
                },
                "required": []
            }
        )

    def execute(self, path: str = ".") -> str:
        """List directory contents"""
        try:
            dir_path = Path(path).expanduser().resolve()
            if not dir_path.exists():
                return f"Error: Directory '{path}' not found"

            if not dir_path.is_dir():
                return f"Error: '{path}' is not a directory"

            items = []
            for item in sorted(dir_path.iterdir()):
                item_type = "DIR " if item.is_dir() else "FILE"
                size = f"{item.stat().st_size:>10}" if item.is_file() else "          "
                items.append(f"{item_type} {size} {item.name}")

            return f"Directory: {path}\n\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {e}"


class RunCommandTool(Tool):
    """Tool to run shell commands"""

    def __init__(self):
        super().__init__(
            name="run_command",
            description="Execute a shell command and return output",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Working directory (optional, default: current)"
                    }
                },
                "required": ["command"]
            }
        )

    def execute(self, command: str, working_dir: str = ".") -> str:
        """Run shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = []
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr}")
            output.append(f"Exit code: {result.returncode}")

            return "\n\n".join(output)
        except subprocess.TimeoutExpired:
            return "Error: Command timed out (30s limit)"
        except Exception as e:
            return f"Error running command: {e}"


class SearchFilesTool(Tool):
    """Tool to search for text in files"""

    def __init__(self):
        super().__init__(
            name="search_files",
            description="Search for text pattern in files using grep",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Text pattern to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to search in (default: current directory)"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "File pattern to match (e.g., '*.py')"
                    }
                },
                "required": ["pattern"]
            }
        )

    def execute(self, pattern: str, path: str = ".", file_pattern: str = "*") -> str:
        """Search for pattern in files"""
        try:
            cmd = f"grep -r -n '{pattern}' --include='{file_pattern}' {path}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return f"Search results for '{pattern}':\n\n{result.stdout}"
            elif result.returncode == 1:
                return f"No matches found for '{pattern}'"
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"Error searching: {e}"


class PythonREPLTool(Tool):
    """Tool to execute Python code"""

    def __init__(self):
        super().__init__(
            name="python_repl",
            description="Execute Python code and return the result",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        )

    def execute(self, code: str) -> str:
        """Execute Python code"""
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # Execute the code
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Clean up
            os.unlink(temp_file)

            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            output.append(f"Exit code: {result.returncode}")

            return "\n\n".join(output)
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (10s limit)"
        except Exception as e:
            return f"Error executing Python code: {e}"


class OpenClawAgent:
    """OpenClaw-style agent with tool calling for Ollama"""

    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.conversation_history: List[Dict[str, Any]] = []

        # Initialize tools
        self.tools: Dict[str, Tool] = {
            "read_file": ReadFileTool(),
            "write_file": WriteFileTool(),
            "list_directory": ListDirectoryTool(),
            "run_command": RunCommandTool(),
            "search_files": SearchFilesTool(),
            "python_repl": PythonREPLTool(),
        }

        print(f"🦅 OpenClaw initialized with {len(self.tools)} tools")
        print(f"📦 Model: {self.model}")
        print(f"🔧 Tools: {', '.join(self.tools.keys())}")

    def get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return """You are OpenClaw, an expert coding assistant with access to tools.

You can:
- Read and write files
- Execute shell commands
- Run Python code
- Search codebases
- List directories

IMPORTANT: When you need to perform an action:
1. Use tools by outputting valid JSON in this format:
   {"tool": "tool_name", "parameters": {"param": "value"}}

2. After receiving tool results, continue the conversation

3. Be proactive - if the user asks to review a file, use read_file first

4. Always explain what you're doing before using tools

Available tools:
- read_file: Read file contents
- write_file: Write/create files
- list_directory: List directory contents
- run_command: Execute shell commands
- search_files: Search text in files
- python_repl: Execute Python code

Example workflow:
User: "Review app.py"
You: "I'll read app.py first."
     {"tool": "read_file", "parameters": {"file_path": "app.py"}}
[Tool result received]
You: "I've reviewed app.py. Here are my findings: ..."
"""

    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool calls from model output"""
        tool_calls = []

        # Look for JSON objects with "tool" key
        json_pattern = r'\{[^}]*"tool"[^}]*\}'
        matches = re.findall(json_pattern, text)

        for match in matches:
            try:
                tool_call = json.loads(match)
                if "tool" in tool_call and "parameters" in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue

        return tool_calls

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool and return the result"""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found"

        tool = self.tools[tool_name]

        try:
            print(f"\n🔧 Executing: {tool_name}({json.dumps(parameters, indent=2)})")
            result = tool.execute(**parameters)
            print(f"✅ Result: {result[:200]}..." if len(result) > 200 else f"✅ Result: {result}")
            return result
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {e}"
            print(f"❌ {error_msg}")
            return error_msg

    def chat(self, user_message: str, max_iterations: int = 5) -> str:
        """Send a message and handle tool calls"""

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Build messages for Ollama
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                *self.conversation_history
            ]

            # Call Ollama API
            print(f"\n💭 Thinking... (iteration {iteration})")
            response = self._call_ollama(messages)

            if not response:
                return "Error: Failed to get response from Ollama"

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            # Check for tool calls
            tool_calls = self.parse_tool_calls(response)

            if not tool_calls:
                # No tool calls, return the response
                return response

            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                result = self.execute_tool(
                    tool_call["tool"],
                    tool_call.get("parameters", {})
                )
                tool_results.append(result)

            # Add tool results to history
            tool_results_text = "\n\n".join([
                f"Tool: {tc['tool']}\nResult: {result}"
                for tc, result in zip(tool_calls, tool_results)
            ])

            self.conversation_history.append({
                "role": "user",
                "content": f"Tool results:\n{tool_results_text}"
            })

        return "Max iterations reached. Please simplify your request."

    def _call_ollama(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=120
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"❌ Error calling Ollama: {e}")
            return None

    def interactive_mode(self):
        """Start interactive chat mode"""
        print("\n" + "="*60)
        print("🦅 OpenClaw for Ollama - Interactive Mode")
        print("="*60)
        print("\nCommands:")
        print("  /help    - Show help")
        print("  /clear   - Clear conversation history")
        print("  /tools   - List available tools")
        print("  /exit    - Exit")
        print("\nTips:")
        print("  - Ask me to read, write, or analyze files")
        print("  - I can execute commands and run Python code")
        print("  - I'll use tools automatically when needed")
        print("="*60)

        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if user_input == "/exit" or user_input == "/quit":
                        print("👋 Goodbye!")
                        break
                    elif user_input == "/clear":
                        self.conversation_history = []
                        print("🗑️  Conversation history cleared")
                        continue
                    elif user_input == "/tools":
                        print("\n🔧 Available tools:")
                        for tool_name, tool in self.tools.items():
                            print(f"  - {tool_name}: {tool.description}")
                        continue
                    elif user_input == "/help":
                        print("""
OpenClaw Help:

Examples:
  "Read app.py and review it"
  "Create a Python script that sorts a list"
  "Search for 'TODO' in all Python files"
  "Run the tests"
  "List files in src/"

I'll automatically use tools when needed!
                        """)
                        continue
                    else:
                        print(f"❌ Unknown command: {user_input}")
                        continue

                # Normal chat with tool support
                print("\n🦅 OpenClaw:", end=" ")
                response = self.chat(user_input)

                # Remove tool call JSON from output
                clean_response = re.sub(r'\{[^}]*"tool"[^}]*\}', '', response).strip()
                if clean_response:
                    print(clean_response)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw for Ollama - Coding agent with tool calling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python openclaw.py

  # One-shot task
  python openclaw.py --task "Review app.py and suggest improvements"

  # Use different model
  python openclaw.py --model qwen2.5-coder:32b

Recommended Models (need tool-calling support):
  - qwen2.5-coder:7b (fast, good balance)
  - qwen2.5-coder:32b (best quality)
  - deepseek-coder-v2:16b (excellent reasoning)
        """
    )

    parser.add_argument("--model", default="qwen2.5-coder:7b",
                       help="Ollama model to use")
    parser.add_argument("--base-url", default="http://localhost:11434",
                       help="Ollama base URL")
    parser.add_argument("--task", help="Single task to execute (non-interactive)")

    args = parser.parse_args()

    # Create agent
    agent = OpenClawAgent(model=args.model, base_url=args.base_url)

    # Check Ollama availability
    try:
        response = requests.get(f"{args.base_url}/api/tags", timeout=2)
        if response.status_code != 200:
            print("❌ Error: Ollama service not responding")
            print("💡 Start Ollama with: ollama serve")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Error: Cannot connect to Ollama")
        print(f"💡 Check if Ollama is running at: {args.base_url}")
        sys.exit(1)

    # Single task mode
    if args.task:
        print(f"\n📋 Task: {args.task}\n")
        response = agent.chat(args.task)
        clean_response = re.sub(r'\{[^}]*"tool"[^}]*\}', '', response).strip()
        print(f"\n🦅 Result:\n{clean_response}")
        sys.exit(0)

    # Interactive mode
    agent.interactive_mode()


if __name__ == "__main__":
    main()
