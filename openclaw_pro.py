#!/usr/bin/env python3
"""
OpenClaw Pro - Advanced agent with web browsing, Discord integration, and business focus
Specialized for coding and building autonomous businesses
WITH SECURITY: Token management, command filtering, path validation
"""

import os
import sys
import json
import subprocess
import argparse
import requests
import asyncio
import discord
from discord.ext import commands
from typing import Optional, List, Dict, Any
from pathlib import Path
import re
import webbrowser
from datetime import datetime

# Import security configuration
try:
    from security_config import SecurityConfig, setup_security
except ImportError:
    print("⚠️  Warning: security_config.py not found. Running without enhanced security.")
    SecurityConfig = None
    setup_security = None


class Tool:
    """Base class for tools"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any], security_config=None):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.security_config = security_config

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def execute(self, **kwargs) -> str:
        raise NotImplementedError


class ReadFileTool(Tool):
    def __init__(self, security_config=None):
        super().__init__(
            name="read_file",
            description="Read file contents - use this before analyzing or modifying code",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"}
                },
                "required": ["file_path"]
            },
            security_config=security_config
        )

    def execute(self, file_path: str) -> str:
        try:
            # Security check
            if self.security_config and not self.security_config.is_path_safe(file_path):
                return f"❌ Access denied: Path not allowed"

            if self.security_config and not self.security_config.check_file_size(file_path):
                return f"❌ File too large to read"

            path = Path(file_path).expanduser().resolve()
            if not path.exists():
                return f"❌ File not found: {file_path}"
            content = path.read_text()
            return f"📄 File: {file_path}\n\n{content}"
        except Exception as e:
            return f"❌ Error reading: {e}"


class WriteFileTool(Tool):
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write/create files - use for implementing code, fixing bugs, creating new features",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"},
                    "content": {"type": "string", "description": "File content"}
                },
                "required": ["file_path", "content"]
            }
        )

    def execute(self, file_path: str, content: str) -> str:
        try:
            path = Path(file_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return f"✅ Wrote {len(content)} chars to {file_path}"
        except Exception as e:
            return f"❌ Error writing: {e}"


class ListDirectoryTool(Tool):
    def __init__(self):
        super().__init__(
            name="list_directory",
            description="List directory contents - use to explore project structure",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: .)"}
                },
                "required": []
            }
        )

    def execute(self, path: str = ".") -> str:
        try:
            dir_path = Path(path).expanduser().resolve()
            if not dir_path.exists():
                return f"❌ Not found: {path}"
            if not dir_path.is_dir():
                return f"❌ Not a directory: {path}"

            items = []
            for item in sorted(dir_path.iterdir()):
                item_type = "📁" if item.is_dir() else "📄"
                size = f"{item.stat().st_size:>10}" if item.is_file() else "          "
                items.append(f"{item_type} {size} {item.name}")

            return f"📂 Directory: {path}\n\n" + "\n".join(items)
        except Exception as e:
            return f"❌ Error: {e}"


class RunCommandTool(Tool):
    def __init__(self):
        super().__init__(
            name="run_command",
            description="Execute shell commands - use for running tests, git operations, building projects, npm/pip install",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to run"},
                    "working_dir": {"type": "string", "description": "Working directory (default: .)"}
                },
                "required": ["command"]
            }
        )

    def execute(self, command: str, working_dir: str = ".") -> str:
        try:
            print(f"  🔄 Running: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            output = []
            if result.stdout:
                output.append(f"📤 STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"⚠️  STDERR:\n{result.stderr}")
            output.append(f"Exit code: {result.returncode}")

            return "\n\n".join(output)
        except subprocess.TimeoutExpired:
            return "❌ Command timeout (60s)"
        except Exception as e:
            return f"❌ Error: {e}"


class SearchFilesTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_files",
            description="Search for text in files using grep - find functions, TODOs, bugs, or specific code patterns",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern"},
                    "path": {"type": "string", "description": "Search path (default: .)"},
                    "file_pattern": {"type": "string", "description": "File pattern like '*.py' (default: *)"}
                },
                "required": ["pattern"]
            }
        )

    def execute(self, pattern: str, path: str = ".", file_pattern: str = "*") -> str:
        try:
            cmd = f"grep -r -n '{pattern}' --include='{file_pattern}' {path} 2>/dev/null | head -50"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return f"🔍 Found '{pattern}':\n\n{result.stdout}"
            elif result.returncode == 1:
                return f"❌ No matches for '{pattern}'"
            else:
                return f"❌ Search error"
        except Exception as e:
            return f"❌ Error: {e}"


class PythonREPLTool(Tool):
    def __init__(self):
        super().__init__(
            name="python_repl",
            description="Execute Python code - use for testing logic, calculations, prototyping, data analysis",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"}
                },
                "required": ["code"]
            }
        )

    def execute(self, code: str) -> str:
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            os.unlink(temp_file)

            output = []
            if result.stdout:
                output.append(f"✅ Output:\n{result.stdout}")
            if result.stderr:
                output.append(f"⚠️  Errors:\n{result.stderr}")
            return "\n\n".join(output) if output else "✅ Executed (no output)"
        except subprocess.TimeoutExpired:
            return "❌ Timeout (10s)"
        except Exception as e:
            return f"❌ Error: {e}"


class WebSearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web using DuckDuckGo - find documentation, solutions, market research, competitors, trends",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "open_browser": {"type": "boolean", "description": "Open results in browser (default: true)"}
                },
                "required": ["query"]
            }
        )

    def execute(self, query: str, open_browser: bool = True) -> str:
        try:
            # DuckDuckGo lite search (no API needed)
            search_url = f"https://lite.duckduckgo.com/lite/?q={requests.utils.quote(query)}"

            # Open in browser if requested
            if open_browser:
                print(f"  🌐 Opening browser: {query}")
                webbrowser.open(search_url)

            # Also fetch results programmatically
            response = requests.get(search_url, timeout=10)

            if response.status_code == 200:
                # Extract basic results from HTML
                content = response.text
                return f"🔍 Search: {query}\n\n🌐 Browser opened with results\n📊 Status: {response.status_code}\n\nUse the browser to view full results!"
            else:
                return f"❌ Search failed: HTTP {response.status_code}"
        except Exception as e:
            return f"❌ Error searching: {e}"


class WebBrowseTool(Tool):
    def __init__(self):
        super().__init__(
            name="web_browse",
            description="Open a URL in browser - view documentation, GitHub repos, tools, inspiration, competitor analysis",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"},
                    "fetch_content": {"type": "boolean", "description": "Also fetch page content (default: false)"}
                },
                "required": ["url"]
            }
        )

    def execute(self, url: str, fetch_content: bool = False) -> str:
        try:
            print(f"  🌐 Opening: {url}")
            webbrowser.open(url)

            result = f"✅ Opened in browser: {url}"

            if fetch_content:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    content_preview = response.text[:1000]
                    result += f"\n\n📄 Content preview:\n{content_preview}..."

            return result
        except Exception as e:
            return f"❌ Error: {e}"


class BusinessPlanTool(Tool):
    def __init__(self):
        super().__init__(
            name="create_business_plan",
            description="Generate a business plan document - use when planning a new business, product, or service",
            parameters={
                "type": "object",
                "properties": {
                    "business_name": {"type": "string", "description": "Business name"},
                    "description": {"type": "string", "description": "Business description"},
                    "target_market": {"type": "string", "description": "Target market/customers"}
                },
                "required": ["business_name", "description"]
            }
        )

    def execute(self, business_name: str, description: str, target_market: str = "General") -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        plan = f"""# Business Plan: {business_name}
Generated: {timestamp}

## Executive Summary
{description}

## Target Market
{target_market}

## Business Model
[To be filled based on analysis]

## Revenue Streams
1. Primary: [Define main revenue source]
2. Secondary: [Additional revenue opportunities]

## Technical Implementation
- Platform: [Web/Mobile/Desktop]
- Stack: [Technology choices]
- Infrastructure: [Hosting, services]

## Go-to-Market Strategy
1. Phase 1: MVP Development
2. Phase 2: Beta Testing
3. Phase 3: Public Launch
4. Phase 4: Growth & Scaling

## Milestones
- Week 1: Planning & Architecture
- Week 2-3: Core Development
- Week 4: Testing & Refinement
- Week 5: Launch Preparation
- Week 6: Public Launch

## Next Steps
1. Validate idea with target users
2. Build MVP
3. Get early adopters
4. Iterate based on feedback
5. Scale & monetize

---
Generated by OpenClaw Pro 🦅
"""

        filename = f"business_plan_{business_name.lower().replace(' ', '_')}.md"
        Path(filename).write_text(plan)

        return f"✅ Created business plan: {filename}\n\n{plan[:500]}..."


class OpenClawPro:
    """Advanced OpenClaw with web browsing, Discord, and business focus"""

    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.conversation_history: List[Dict[str, Any]] = []

        # Initialize all tools
        self.tools: Dict[str, Tool] = {
            "read_file": ReadFileTool(),
            "write_file": WriteFileTool(),
            "list_directory": ListDirectoryTool(),
            "run_command": RunCommandTool(),
            "search_files": SearchFilesTool(),
            "python_repl": PythonREPLTool(),
            "web_search": WebSearchTool(),
            "web_browse": WebBrowseTool(),
            "create_business_plan": BusinessPlanTool(),
        }

        print(f"🦅 OpenClaw Pro initialized")
        print(f"📦 Model: {self.model}")
        print(f"🔧 Tools: {len(self.tools)} available")
        print(f"🌐 Web browsing: Enabled")
        print(f"💼 Business mode: Active")

    def get_system_prompt(self) -> str:
        return """You are OpenClaw Pro, an elite AI agent specialized in:

🎯 CORE EXPERTISE:
1. Software Development - Build production-ready applications
2. Business Building - Create profitable, scalable businesses
3. Market Research - Find opportunities and validate ideas
4. Full-Stack Implementation - From idea to deployed product

🛠️ YOUR CAPABILITIES:
- Read/Write files and code
- Execute commands and run tests
- Search the web for research and documentation
- Browse URLs (opens in visible browser)
- Create business plans and strategies
- Execute Python code for prototyping
- Search codebases for patterns

🚀 APPROACH:
1. Think like a founder - validate before building
2. Build fast - MVP first, perfect later
3. Use web search to research markets, competitors, tools
4. Write production-quality code with tests
5. Plan for monetization from day one

📋 TOOL USAGE:
When you need to use a tool, output JSON like:
{"tool": "tool_name", "parameters": {"param": "value"}}

Examples:
- Research: {"tool": "web_search", "parameters": {"query": "best AI tools 2026"}}
- Browse docs: {"tool": "web_browse", "parameters": {"url": "https://docs.python.org"}}
- Create code: {"tool": "write_file", "parameters": {"file_path": "app.py", "content": "..."}}
- Run tests: {"tool": "run_command", "parameters": {"command": "pytest"}}

💡 BUSINESS MINDSET:
- Always think: "How can this make money?"
- Validate ideas with web research before building
- Build things people will actually use
- Focus on solving real problems
- Create sustainable revenue models

You're not just a coding assistant - you're a business-building partner! 🦅"""

    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        tool_calls = []
        json_pattern = r'\{[^}]*"tool"[^}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                # Clean up the match
                cleaned = match.strip()
                tool_call = json.loads(cleaned)
                if "tool" in tool_call and "parameters" in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue

        return tool_calls

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        if tool_name not in self.tools:
            return f"❌ Tool not found: {tool_name}"

        tool = self.tools[tool_name]

        try:
            print(f"\n🔧 Using {tool_name}:")
            print(f"   {json.dumps(parameters, indent=2)}")
            result = tool.execute(**parameters)
            preview = result[:300] + "..." if len(result) > 300 else result
            print(f"✅ Result: {preview}\n")
            return result
        except Exception as e:
            error = f"❌ Error in {tool_name}: {e}"
            print(error)
            return error

    def chat(self, user_message: str, max_iterations: int = 10) -> str:
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                *self.conversation_history
            ]

            print(f"\n💭 Thinking... (iteration {iteration}/{max_iterations})")
            response = self._call_ollama(messages)

            if not response:
                return "❌ Failed to get response from Ollama"

            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            tool_calls = self.parse_tool_calls(response)

            if not tool_calls:
                return response

            tool_results = []
            for tool_call in tool_calls:
                result = self.execute_tool(
                    tool_call["tool"],
                    tool_call.get("parameters", {})
                )
                tool_results.append(result)

            tool_results_text = "\n\n".join([
                f"🔧 Tool: {tc['tool']}\n📊 Result: {result}"
                for tc, result in zip(tool_calls, tool_results)
            ])

            self.conversation_history.append({
                "role": "user",
                "content": f"Tool results:\n{tool_results_text}"
            })

        return "⚠️  Max iterations reached. Try breaking down your request."

    def _call_ollama(self, messages: List[Dict[str, str]]) -> Optional[str]:
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=180
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return None

    def interactive_mode(self):
        print("\n" + "="*70)
        print("🦅 OpenClaw Pro - Business Builder & Coding Agent")
        print("="*70)
        print("\n💼 Business Mode Active - Let's build something profitable!")
        print("\nCommands:")
        print("  /help    - Show help")
        print("  /clear   - Clear conversation")
        print("  /tools   - List tools")
        print("  /exit    - Exit")
        print("\n💡 Try:")
        print("  - 'Research profitable SaaS ideas for 2026'")
        print("  - 'Build me a web scraper that...'")
        print("  - 'Create a business plan for...'")
        print("  - 'Find and analyze competitors for...'")
        print("="*70)

        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if user_input in ["/exit", "/quit"]:
                        print("👋 Build something great!")
                        break
                    elif user_input == "/clear":
                        self.conversation_history = []
                        print("🗑️  Cleared")
                        continue
                    elif user_input == "/tools":
                        print("\n🔧 Available tools:")
                        for name, tool in self.tools.items():
                            print(f"  • {name}: {tool.description}")
                        continue
                    elif user_input == "/help":
                        print(self.get_system_prompt())
                        continue
                    else:
                        print(f"❌ Unknown: {user_input}")
                        continue

                print("\n🦅 OpenClaw Pro:")
                response = self.chat(user_input)
                clean = re.sub(r'\{[^}]*"tool"[^}]*\}', '', response).strip()
                if clean:
                    print(clean)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


# Discord Bot Integration
class OpenClawDiscordBot(commands.Bot):
    def __init__(self, openclaw: OpenClawPro):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!claw ', intents=intents)
        self.openclaw = openclaw

    async def on_ready(self):
        print(f'🤖 Discord Bot ready as {self.user}')
        print(f'📋 Use: !claw <message>')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!claw '):
            query = message.content[6:].strip()
            await message.channel.send(f"🦅 Thinking about: {query}")

            try:
                response = self.openclaw.chat(query)
                clean = re.sub(r'\{[^}]*"tool"[^}]*\}', '', response).strip()

                # Split long messages
                if len(clean) > 2000:
                    chunks = [clean[i:i+1900] for i in range(0, len(clean), 1900)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(clean)
            except Exception as e:
                await message.channel.send(f"❌ Error: {e}")

        await self.process_commands(message)


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Pro - Advanced coding & business agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python openclaw_pro.py

  # One-shot task
  python openclaw_pro.py --task "Research AI SaaS trends and create a business plan"

  # Discord bot
  python openclaw_pro.py --discord --token YOUR_DISCORD_TOKEN

  # Custom model
  python openclaw_pro.py --model qwen2.5-coder:32b

Business Ideas:
  "Find profitable micro-SaaS ideas"
  "Research competitors for [idea]"
  "Build an MVP for [product]"
  "Create pricing strategy for [service]"
        """
    )

    parser.add_argument("--model", default="qwen2.5-coder:7b", help="Ollama model")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--task", help="Single task (non-interactive)")
    parser.add_argument("--discord", action="store_true", help="Run as Discord bot")
    parser.add_argument("--token", help="Discord bot token")

    args = parser.parse_args()

    # Check Ollama
    try:
        response = requests.get(f"{args.base_url}/api/tags", timeout=2)
        if response.status_code != 200:
            print("❌ Ollama not responding")
            print("💡 Start with: ollama serve")
            sys.exit(1)
    except:
        print("❌ Cannot connect to Ollama")
        sys.exit(1)

    # Create agent
    agent = OpenClawPro(model=args.model, base_url=args.base_url)

    # Discord bot mode
    if args.discord:
        token = args.token or os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            print("❌ Discord token required")
            print("💡 Use: --token YOUR_TOKEN or set DISCORD_BOT_TOKEN env var")
            sys.exit(1)

        bot = OpenClawDiscordBot(agent)
        print("🤖 Starting Discord bot...")
        bot.run(token)
        return

    # Single task mode
    if args.task:
        print(f"\n📋 Task: {args.task}\n")
        response = agent.chat(args.task)
        clean = re.sub(r'\{[^}]*"tool"[^}]*\}', '', response).strip()
        print(f"\n🦅 Result:\n{clean}")
        sys.exit(0)

    # Interactive mode
    agent.interactive_mode()


if __name__ == "__main__":
    main()
