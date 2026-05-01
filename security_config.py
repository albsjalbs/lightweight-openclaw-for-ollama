#!/usr/bin/env python3
"""
Security configuration and utilities for OpenClaw Pro
Handles secure token storage, environment variables, and safety checks
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import hashlib


class SecurityConfig:
    """Secure configuration management for OpenClaw Pro"""

    def __init__(self):
        self.env_file = Path(".env")
        self.secrets_file = Path(".secrets.json")
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load configuration from .env file and environment variables"""
        # Load from .env file if exists
        if self.env_file.exists():
            self._load_env_file()

        # Environment variables override .env file
        self.config = {
            "discord_token": os.getenv("DISCORD_BOT_TOKEN"),
            "ollama_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
            "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "10")),
            "allowed_directories": os.getenv("ALLOWED_DIRECTORIES", ".").split(","),
            "restricted_commands": os.getenv("RESTRICTED_COMMANDS", "rm -rf,dd,mkfs,format").split(","),
            "business_plan_dir": os.getenv("DEFAULT_BUSINESS_PLAN_DIR", "./business_plans"),
            "auto_save_research": os.getenv("AUTO_SAVE_RESEARCH", "true").lower() == "true",
        }

    def _load_env_file(self):
        """Load environment variables from .env file"""
        try:
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Warning: Could not load .env file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def get_discord_token(self) -> Optional[str]:
        """Get Discord bot token securely"""
        token = self.config.get("discord_token")

        if not token:
            print("\n❌ Discord bot token not found!")
            print("\n💡 To set up Discord bot token:")
            print("   1. Create .env file (copy from .env.example)")
            print("   2. Add: DISCORD_BOT_TOKEN=your_token_here")
            print("   3. Or set environment variable:")
            print("      export DISCORD_BOT_TOKEN='your_token'")
            print("\n🔗 Get token: https://discord.com/developers/applications\n")
            return None

        # Validate token format (Discord tokens have specific format)
        if not self._validate_discord_token(token):
            print("⚠️  Warning: Discord token format looks invalid")

        return token

    def _validate_discord_token(self, token: str) -> bool:
        """Validate Discord token format"""
        # Discord tokens are typically 59+ characters
        if len(token) < 50:
            return False

        # Should not contain obvious placeholder text
        placeholders = ["your_token", "your_discord", "example", "xxx", "paste_here"]
        if any(p in token.lower() for p in placeholders):
            return False

        return True

    def is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute"""
        command_lower = command.lower()

        # Check for restricted commands
        restricted = self.config.get("restricted_commands", [])
        for restricted_cmd in restricted:
            if restricted_cmd.lower() in command_lower:
                print(f"⚠️  Blocked restricted command: {restricted_cmd}")
                return False

        # Warn about potentially dangerous commands
        dangerous_patterns = [
            "rm -rf /",
            "dd if=",
            "mkfs",
            "> /dev/",
            "chmod 777",
            "chown -R",
            "sudo rm",
        ]

        for pattern in dangerous_patterns:
            if pattern in command_lower:
                print(f"⚠️  Warning: Potentially dangerous command detected: {pattern}")
                response = input("   Continue anyway? (yes/no): ").strip().lower()
                if response != "yes":
                    print("   ❌ Command blocked by user")
                    return False

        return True

    def is_path_safe(self, file_path: str) -> bool:
        """Check if file path is safe to access"""
        try:
            path = Path(file_path).resolve()

            # Check if path is within allowed directories
            allowed_dirs = self.config.get("allowed_directories", ["."])

            # If "." is in allowed, allow anything in current directory tree
            if "." in allowed_dirs:
                cwd = Path.cwd().resolve()
                if not str(path).startswith(str(cwd)):
                    print(f"⚠️  Warning: Path outside working directory: {file_path}")
                    return False

            # Don't allow access to system directories
            system_dirs = ["/etc", "/sys", "/proc", "/dev", "/boot", "/root"]
            for sys_dir in system_dirs:
                if str(path).startswith(sys_dir):
                    print(f"❌ Blocked access to system directory: {sys_dir}")
                    return False

            return True

        except Exception as e:
            print(f"❌ Path validation error: {e}")
            return False

    def check_file_size(self, file_path: str) -> bool:
        """Check if file size is within limits"""
        try:
            path = Path(file_path)
            if not path.exists():
                return True  # New files are OK

            size_mb = path.stat().st_size / (1024 * 1024)
            max_size = self.config.get("max_file_size_mb", 10)

            if size_mb > max_size:
                print(f"⚠️  Warning: File size ({size_mb:.1f}MB) exceeds limit ({max_size}MB)")
                return False

            return True

        except Exception:
            return True  # If can't check, allow

    def sanitize_url(self, url: str) -> Optional[str]:
        """Sanitize and validate URL"""
        # Remove any potential injection attempts
        url = url.strip()

        # Check for valid URL schemes
        if not url.startswith(("http://", "https://")):
            print(f"❌ Invalid URL scheme. Must start with http:// or https://")
            return None

        # Block potentially dangerous URLs
        blocked_domains = ["file://", "javascript:", "data:", "vbscript:"]
        if any(blocked in url.lower() for blocked in blocked_domains):
            print(f"❌ Blocked potentially dangerous URL")
            return None

        return url

    def create_env_file_interactive(self):
        """Interactive setup to create .env file"""
        print("\n🔧 OpenClaw Pro Security Setup")
        print("=" * 60)

        if self.env_file.exists():
            print(f"\n⚠️  .env file already exists at: {self.env_file}")
            response = input("   Overwrite? (yes/no): ").strip().lower()
            if response != "yes":
                print("   ℹ️  Keeping existing .env file")
                return

        print("\n📋 Let's set up your configuration:")

        # Discord token (optional)
        print("\n1️⃣  Discord Bot Token (optional - press Enter to skip)")
        print("   Get token: https://discord.com/developers/applications")
        discord_token = input("   Token: ").strip()

        # Ollama settings
        print("\n2️⃣  Ollama Configuration")
        ollama_url = input("   Ollama URL (default: http://localhost:11434): ").strip()
        if not ollama_url:
            ollama_url = "http://localhost:11434"

        ollama_model = input("   Model (default: qwen2.5-coder:7b): ").strip()
        if not ollama_model:
            ollama_model = "qwen2.5-coder:7b"

        # Create .env file
        env_content = f"""# OpenClaw Pro Configuration
# Generated: {Path.cwd()}

# Discord Bot (optional)
DISCORD_BOT_TOKEN={discord_token if discord_token else ""}

# Ollama Settings
OLLAMA_BASE_URL={ollama_url}
OLLAMA_MODEL={ollama_model}

# Security Settings
MAX_FILE_SIZE_MB=10
ALLOWED_DIRECTORIES=.
RESTRICTED_COMMANDS=rm -rf,dd,mkfs,format

# Business Settings
DEFAULT_BUSINESS_PLAN_DIR=./business_plans
AUTO_SAVE_RESEARCH=true
"""

        try:
            with open(self.env_file, "w") as f:
                f.write(env_content)

            print(f"\n✅ Created .env file at: {self.env_file}")
            print("\n⚠️  IMPORTANT:")
            print("   - This file contains secrets - never commit to git!")
            print("   - .env is already in .gitignore")
            print("   - Share .env.example instead")
            print("\n✅ Setup complete! You can now run OpenClaw Pro.")

        except Exception as e:
            print(f"\n❌ Error creating .env file: {e}")


def setup_security():
    """Initialize security configuration"""
    config = SecurityConfig()

    # Check if .env exists, if not offer to create it
    if not config.env_file.exists() and not os.getenv("DISCORD_BOT_TOKEN"):
        print("\n💡 No .env file found. Would you like to create one?")
        response = input("   (yes/no): ").strip().lower()
        if response == "yes":
            config.create_env_file_interactive()
            config.load_config()  # Reload after creation

    return config


if __name__ == "__main__":
    # Run interactive setup
    config = SecurityConfig()
    config.create_env_file_interactive()
