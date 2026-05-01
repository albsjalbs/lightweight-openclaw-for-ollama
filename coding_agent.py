#!/usr/bin/env python3
"""
Lightweight Local Coding Assistant using Ollama
A fast, local alternative to Claude for coding tasks
"""

import sys
import json
import argparse
import requests
from typing import Optional, List, Dict
from pathlib import Path


class OllamaCodingAgent:
    """Lightweight coding assistant powered by local Ollama models"""

    def __init__(self, model: str = "codellama", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.conversation_history: List[Dict[str, str]] = []

    def check_ollama_available(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except requests.exceptions.RequestException:
            return []

    def chat(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = True) -> str:
        """Send a chat message to Ollama"""

        # Build messages
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        messages.extend(self.conversation_history)

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        # Make API request
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=stream,
                timeout=300
            )

            if stream:
                full_response = ""
                print("Assistant: ", end="", flush=True)
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if 'message' in chunk:
                            content = chunk['message'].get('content', '')
                            print(content, end="", flush=True)
                            full_response += content
                        if chunk.get('done', False):
                            print()  # New line at end
                            break

                # Update conversation history
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": full_response})

                return full_response
            else:
                result = response.json()
                assistant_message = result['message']['content']

                # Update conversation history
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": assistant_message})

                return assistant_message

        except requests.exceptions.RequestException as e:
            return f"Error communicating with Ollama: {e}"

    def analyze_code(self, code: str, task: str = "explain") -> str:
        """Analyze code with specific task"""
        tasks = {
            "explain": "Explain what this code does in detail:",
            "review": "Review this code for bugs, improvements, and best practices:",
            "optimize": "Suggest optimizations for this code:",
            "debug": "Help debug this code and identify potential issues:",
            "refactor": "Suggest refactoring improvements for this code:"
        }

        task_prompt = tasks.get(task, tasks["explain"])
        prompt = f"{task_prompt}\n\n```\n{code}\n```"

        return self.chat(prompt, system_prompt=self.get_coding_system_prompt())

    def analyze_file(self, filepath: str, task: str = "explain") -> str:
        """Analyze a code file"""
        try:
            path = Path(filepath)
            if not path.exists():
                return f"Error: File '{filepath}' not found"

            code = path.read_text()
            print(f"\n📁 Analyzing: {filepath}")
            print(f"📊 Task: {task}")
            print("-" * 60)

            return self.analyze_code(code, task)

        except Exception as e:
            return f"Error reading file: {e}"

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

    def interactive_mode(self):
        """Start interactive chat mode"""
        print("🤖 Lightweight Coding Assistant (Ollama)")
        print(f"📦 Model: {self.model}")
        print("💡 Commands: /help, /clear, /models, /exit")
        print("-" * 60)

        while True:
            try:
                user_input = input("\nYou: ").strip()

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
                    elif user_input == "/models":
                        models = self.list_models()
                        print(f"📦 Available models: {', '.join(models)}")
                        continue
                    elif user_input == "/help":
                        print("""
Commands:
  /help    - Show this help message
  /clear   - Clear conversation history
  /models  - List available models
  /exit    - Exit the assistant

Coding tasks:
  - Ask coding questions
  - Request code explanations
  - Get debugging help
  - Code review suggestions
  - Optimization tips
                        """)
                        continue
                    else:
                        print(f"❌ Unknown command: {user_input}")
                        continue

                # Normal chat
                self.chat(user_input, system_prompt=self.get_coding_system_prompt())

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Lightweight Local Coding Assistant using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python coding_agent.py

  # Analyze a file
  python coding_agent.py --file script.py --task review

  # One-shot question
  python coding_agent.py --prompt "How do I reverse a string in Python?"

  # Use different model
  python coding_agent.py --model deepseek-coder
        """
    )

    parser.add_argument("--model", default="codellama",
                       help="Ollama model to use (default: codellama)")
    parser.add_argument("--base-url", default="http://localhost:11434",
                       help="Ollama base URL (default: http://localhost:11434)")
    parser.add_argument("--file", help="Code file to analyze")
    parser.add_argument("--task", default="explain",
                       choices=["explain", "review", "optimize", "debug", "refactor"],
                       help="Task to perform on the file")
    parser.add_argument("--prompt", help="Single prompt (non-interactive)")
    parser.add_argument("--list-models", action="store_true",
                       help="List available Ollama models")

    args = parser.parse_args()

    # Create agent
    agent = OllamaCodingAgent(model=args.model, base_url=args.base_url)

    # Check Ollama availability
    if not agent.check_ollama_available():
        print("❌ Error: Ollama service not running")
        print("💡 Start Ollama with: ollama serve")
        print(f"💡 Or check if Ollama is running at: {args.base_url}")
        sys.exit(1)

    # List models
    if args.list_models:
        models = agent.list_models()
        if models:
            print("📦 Available Ollama models:")
            for model in models:
                print(f"  - {model}")
        else:
            print("❌ No models found. Install with: ollama pull codellama")
        sys.exit(0)

    # File analysis mode
    if args.file:
        agent.analyze_file(args.file, args.task)
        sys.exit(0)

    # Single prompt mode
    if args.prompt:
        agent.chat(args.prompt, system_prompt=agent.get_coding_system_prompt())
        sys.exit(0)

    # Interactive mode (default)
    agent.interactive_mode()


if __name__ == "__main__":
    main()
