#!/usr/bin/env python3
"""
Obsidian-based memory system for OpenClaw Pro
Uses Obsidian vault as graph database for persistent memory across sessions
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib


class ObsidianMemory:
    """Obsidian vault-based memory system"""

    def __init__(self, vault_path: str = "./openclaw_memory"):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(exist_ok=True)

        # Create folder structure
        self.conversations_dir = self.vault_path / "Conversations"
        self.projects_dir = self.vault_path / "Projects"
        self.code_snippets_dir = self.vault_path / "Code Snippets"
        self.business_plans_dir = self.vault_path / "Business Plans"
        self.learnings_dir = self.vault_path / "Learnings"

        for dir in [self.conversations_dir, self.projects_dir,
                    self.code_snippets_dir, self.business_plans_dir,
                    self.learnings_dir]:
            dir.mkdir(exist_ok=True)

        # Index file
        self.index_file = self.vault_path / "INDEX.md"
        self.ensure_index()

    def ensure_index(self):
        """Ensure index file exists"""
        if not self.index_file.exists():
            content = """# OpenClaw Pro Memory Index

This vault contains OpenClaw Pro's persistent memory across sessions.

## Structure

- [[Conversations]] - Chat history and interactions
- [[Projects]] - Project details and progress
- [[Code Snippets]] - Useful code examples
- [[Business Plans]] - Business strategies and plans
- [[Learnings]] - Knowledge accumulated over time

## Quick Links

### Recent Conversations
(Auto-updated)

### Active Projects
(Auto-updated)

### Key Learnings
(Auto-updated)

---
*Last Updated: {date}*
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M"))

            self.index_file.write_text(content)

    def save_conversation(self, user_id: str, messages: List[Dict[str, str]]) -> str:
        """Save conversation to Obsidian vault"""
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H-%M-%S")

        filename = f"{date_str}_{time_str}_{user_id[:8]}.md"
        file_path = self.conversations_dir / filename

        # Create conversation note
        content = f"""# Conversation - {timestamp.strftime("%Y-%m-%d %H:%M:%S")}

**User ID**: {user_id}
**Date**: {date_str}
**Tags**: #conversation #openclaw

## Messages

"""

        for msg in messages:
            role = msg.get("role", "unknown")
            content_text = msg.get("content", "")

            if role == "user":
                content += f"\n### 👤 User\n\n{content_text}\n"
            elif role == "assistant":
                content += f"\n### 🦅 OpenClaw\n\n{content_text}\n"
            elif role == "system":
                content += f"\n### ⚙️ System\n\n{content_text}\n"

        # Add links
        content += "\n\n## Links\n\n"
        content += "- [[INDEX|Back to Index]]\n"

        file_path.write_text(content)
        return str(file_path)

    def save_project(
        self,
        project_name: str,
        description: str,
        status: str = "active",
        files: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Save project information"""
        filename = f"{project_name.replace(' ', '_')}.md"
        file_path = self.projects_dir / filename

        metadata = metadata or {}
        files = files or []

        content = f"""# Project: {project_name}

**Status**: {status}
**Created**: {datetime.now().strftime("%Y-%m-%d")}
**Tags**: #project #openclaw

## Description

{description}

## Files

"""

        for file in files:
            content += f"- `{file}`\n"

        content += "\n## Metadata\n\n```json\n"
        content += json.dumps(metadata, indent=2)
        content += "\n```\n"

        content += "\n## Progress\n\n"
        content += "- [ ] Planning\n"
        content += "- [ ] Development\n"
        content += "- [ ] Testing\n"
        content += "- [ ] Deployment\n"

        content += "\n\n## Links\n\n"
        content += "- [[INDEX|Back to Index]]\n"

        file_path.write_text(content)
        return str(file_path)

    def save_code_snippet(
        self,
        title: str,
        code: str,
        language: str = "python",
        description: str = "",
        tags: List[str] = None
    ) -> str:
        """Save code snippet"""
        tags = tags or []
        filename = f"{title.replace(' ', '_')}.md"
        file_path = self.code_snippets_dir / filename

        tag_str = " ".join([f"#{tag}" for tag in tags])

        content = f"""# Code: {title}

**Language**: {language}
**Tags**: #code #snippet {tag_str}

## Description

{description}

## Code

```{language}
{code}
```

## Links

- [[INDEX|Back to Index]]
"""

        file_path.write_text(content)
        return str(file_path)

    def save_learning(
        self,
        topic: str,
        content: str,
        category: str = "general",
        related_to: List[str] = None
    ) -> str:
        """Save learning/knowledge"""
        related_to = related_to or []
        filename = f"{topic.replace(' ', '_')}.md"
        file_path = self.learnings_dir / filename

        note_content = f"""# Learning: {topic}

**Category**: {category}
**Date**: {datetime.now().strftime("%Y-%m-%d")}
**Tags**: #learning #{category}

## Content

{content}

## Related Topics

"""

        for related in related_to:
            note_content += f"- [[{related}]]\n"

        note_content += "\n## Links\n\n"
        note_content += "- [[INDEX|Back to Index]]\n"

        file_path.write_text(note_content)
        return str(file_path)

    def save_business_plan(
        self,
        business_name: str,
        plan_content: str
    ) -> str:
        """Save business plan"""
        filename = f"{business_name.replace(' ', '_')}_plan.md"
        file_path = self.business_plans_dir / filename

        content = f"""# Business Plan: {business_name}

**Created**: {datetime.now().strftime("%Y-%m-%d")}
**Tags**: #business #plan

{plan_content}

## Links

- [[INDEX|Back to Index]]
"""

        file_path.write_text(content)
        return str(file_path)

    def search_notes(self, query: str) -> List[str]:
        """Search notes by content"""
        results = []

        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text().lower()
                if query.lower() in content:
                    results.append(str(md_file.relative_to(self.vault_path)))
            except:
                pass

        return results

    def get_recent_conversations(self, limit: int = 5) -> List[str]:
        """Get recent conversation files"""
        conversations = sorted(
            self.conversations_dir.glob("*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        return [str(f.relative_to(self.vault_path)) for f in conversations[:limit]]

    def get_active_projects(self) -> List[str]:
        """Get active project files"""
        projects = []

        for project_file in self.projects_dir.glob("*.md"):
            content = project_file.read_text()
            if "**Status**: active" in content:
                projects.append(str(project_file.relative_to(self.vault_path)))

        return projects

    def update_index(self):
        """Update index with recent items"""
        recent_convs = self.get_recent_conversations(5)
        active_projs = self.get_active_projects()

        content = f"""# OpenClaw Pro Memory Index

This vault contains OpenClaw Pro's persistent memory across sessions.

## Structure

- [[Conversations]] - Chat history and interactions
- [[Projects]] - Project details and progress
- [[Code Snippets]] - Useful code examples
- [[Business Plans]] - Business strategies and plans
- [[Learnings]] - Knowledge accumulated over time

## Quick Links

### Recent Conversations

"""

        for conv in recent_convs:
            content += f"- [[{conv}]]\n"

        content += "\n### Active Projects\n\n"

        for proj in active_projs:
            content += f"- [[{proj}]]\n"

        content += f"\n---\n*Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"

        self.index_file.write_text(content)


# Singleton instance
obsidian_memory = ObsidianMemory()
