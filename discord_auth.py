#!/usr/bin/env python3
"""
Discord Authentication and Authorization for OpenClaw Pro
Password-protected bot access with user management
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Set


class DiscordAuth:
    """Discord bot authentication and authorization"""

    def __init__(self, password: str = "504846"):
        self.password_hash = self._hash_password(password)
        self.auth_file = Path(".discord_auth.json")
        self.authorized_users: Dict[str, dict] = {}
        self.session_timeout = timedelta(hours=24)
        self.load_authorized_users()

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def load_authorized_users(self):
        """Load authorized users from file"""
        if self.auth_file.exists():
            try:
                with open(self.auth_file) as f:
                    data = json.load(f)
                    self.authorized_users = data.get("users", {})
            except Exception as e:
                print(f"⚠️  Error loading auth data: {e}")
                self.authorized_users = {}

    def save_authorized_users(self):
        """Save authorized users to file"""
        try:
            data = {
                "users": self.authorized_users,
                "updated": datetime.now().isoformat()
            }
            with open(self.auth_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving auth data: {e}")

    def authenticate(self, user_id: str, password: str) -> bool:
        """Authenticate user with password"""
        password_hash = self._hash_password(password)

        if password_hash == self.password_hash:
            # Successful authentication
            self.authorized_users[user_id] = {
                "authenticated_at": datetime.now().isoformat(),
                "username": None,  # Will be filled in later
                "permissions": ["read", "write", "execute"]
            }
            self.save_authorized_users()
            return True

        return False

    def is_authorized(self, user_id: str) -> bool:
        """Check if user is authorized"""
        if user_id not in self.authorized_users:
            return False

        # Check session timeout
        auth_time = datetime.fromisoformat(
            self.authorized_users[user_id]["authenticated_at"]
        )

        if datetime.now() - auth_time > self.session_timeout:
            # Session expired
            del self.authorized_users[user_id]
            self.save_authorized_users()
            return False

        return True

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        if not self.is_authorized(user_id):
            return False

        return permission in self.authorized_users[user_id].get("permissions", [])

    def logout(self, user_id: str):
        """Logout user"""
        if user_id in self.authorized_users:
            del self.authorized_users[user_id]
            self.save_authorized_users()

    def get_user_info(self, user_id: str) -> Optional[dict]:
        """Get user information"""
        return self.authorized_users.get(user_id)

    def update_username(self, user_id: str, username: str):
        """Update username for user"""
        if user_id in self.authorized_users:
            self.authorized_users[user_id]["username"] = username
            self.save_authorized_users()


class FileOperationConfirmation:
    """Confirmation system for file operations"""

    def __init__(self):
        self.pending_confirmations: Dict[str, dict] = {}

    def request_confirmation(
        self,
        user_id: str,
        operation: str,
        file_path: str,
        details: str = ""
    ) -> str:
        """Request confirmation for file operation"""
        confirmation_id = f"{user_id}_{operation}_{file_path}_{datetime.now().timestamp()}"

        self.pending_confirmations[confirmation_id] = {
            "user_id": user_id,
            "operation": operation,
            "file_path": file_path,
            "details": details,
            "created_at": datetime.now().isoformat()
        }

        return confirmation_id

    def get_confirmation(self, confirmation_id: str) -> Optional[dict]:
        """Get pending confirmation"""
        return self.pending_confirmations.get(confirmation_id)

    def confirm(self, confirmation_id: str) -> bool:
        """Confirm operation"""
        if confirmation_id in self.pending_confirmations:
            del self.pending_confirmations[confirmation_id]
            return True
        return False

    def cancel(self, confirmation_id: str) -> bool:
        """Cancel operation"""
        if confirmation_id in self.pending_confirmations:
            del self.pending_confirmations[confirmation_id]
            return True
        return False

    def cleanup_expired(self, max_age_minutes: int = 5):
        """Clean up expired confirmation requests"""
        now = datetime.now()
        expired = []

        for conf_id, conf_data in self.pending_confirmations.items():
            created = datetime.fromisoformat(conf_data["created_at"])
            if (now - created).total_seconds() > max_age_minutes * 60:
                expired.append(conf_id)

        for conf_id in expired:
            del self.pending_confirmations[conf_id]


# Singleton instances
discord_auth = DiscordAuth()
file_confirmation = FileOperationConfirmation()
