"""
system_tools.py - Safe system and project tools for VERONICA.
Includes Date/Time, File Listing, File Reading, and Project Searching.
Restricted strictly to the project directory to prevent security risks.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from config.settings import settings
from tools.base import BaseTool


def _resolve_safe_path(target_path: str) -> Path:
    """
    Resolves target_path relative to PROJECT_ROOT and ensures it does not
    escape the project directory (directory traversal protection).
    """
    root = settings.PROJECT_ROOT.resolve()
    requested = (root / target_path).resolve()

    if not str(requested).startswith(str(root)):
        raise PermissionError("Access denied: Path is outside the project workspace.")

    # Guard against reading .env directly via tool to protect secrets
    if requested.name == ".env":
        raise PermissionError("Access denied: Protected configuration file cannot be read via tools.")

    return requested


class DateTimeTool(BaseTool):
    """Tool to provide the current local date, time, and day of week."""

    name = "get_current_datetime"
    description = "Retrieves the current local date, time, and day of the week."
    parameters = {
        "type": "object",
        "properties": {},
    }

    def execute(self, **kwargs) -> str:
        now = datetime.now()
        return (
            f"Current Date: {now.strftime('%Y-%m-%d')}\n"
            f"Current Time: {now.strftime('%H:%M:%S')}\n"
            f"Day of Week: {now.strftime('%A')}"
        )


class ListFilesTool(BaseTool):
    """Safe tool to list files within the project folder."""

    name = "list_project_files"
    description = "Lists files and directories inside the project workspace or a specified subfolder."
    parameters = {
        "type": "object",
        "properties": {
            "subfolder": {
                "type": "string",
                "description": "Optional relative subfolder path (default is project root).",
                "default": "",
            }
        },
    }

    def execute(self, subfolder: str = "", **kwargs) -> str:
        try:
            target_dir = _resolve_safe_path(subfolder)
            if not target_dir.is_dir():
                return f"Error: '{subfolder}' is not a directory."

            items = []
            for item in sorted(target_dir.iterdir()):
                # Filter out heavy virtual environment or git folders from cluttering
                if item.name in (".venv", ".git", "__pycache__"):
                    continue
                type_indicator = "[DIR] " if item.is_dir() else "[FILE]"
                items.append(f"{type_indicator} {item.name}")

            if not items:
                return f"Directory '{target_dir.name}' is empty."

            return f"Contents of '{target_dir.relative_to(settings.PROJECT_ROOT)}':\n" + "\n".join(items)
        except PermissionError as pe:
            return f"Security Restriction: {pe}"
        except Exception as e:
            return f"Error listing directory: {e}"


class ReadFileTool(BaseTool):
    """Safe tool to read text files inside the project folder."""

    name = "read_project_file"
    description = "Reads the content of a text file located within the project directory."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The relative path of the file to read (e.g., 'README.md' or 'config/settings.py').",
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read (default 100).",
                "default": 100,
            },
        },
        "required": ["file_path"],
    }

    def execute(self, file_path: str = "", max_lines: int = 100, **kwargs) -> str:
        try:
            target_file = _resolve_safe_path(file_path)

            if not target_file.exists():
                return f"Error: File '{file_path}' does not exist."
            if not target_file.is_file():
                return f"Error: Path '{file_path}' is a directory, not a file."

            # Check file size (limit to 500 KB to avoid memory issues)
            if target_file.stat().st_size > 500 * 1024:
                return f"Error: File '{file_path}' is too large to read safely."

            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(max_lines)]
                content = "".join(lines)

            total_lines_read = len(lines)
            return (
                f"File: {file_path} ({total_lines_read} lines read)\n"
                f"----------------------------------------\n"
                f"{content}"
            )
        except PermissionError as pe:
            return f"Security Restriction: {pe}"
        except Exception as e:
            return f"Error reading file: {e}"


class SearchFilesTool(BaseTool):
    """Tool to search for text patterns across project files."""

    name = "search_project_files"
    description = "Searches for a keyword or string within files in the project workspace."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search term or query string.",
            },
            "file_extension": {
                "type": "string",
                "description": "Optional file extension to restrict search (e.g. '.py', '.txt', '.md').",
                "default": "",
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str = "", file_extension: str = "", **kwargs) -> str:
        if not query or not query.strip():
            return "Error: Search query cannot be empty."

        query_clean = query.strip().lower()
        ext_filter = file_extension.strip().lower() if file_extension else None
        matches = []
        root = settings.PROJECT_ROOT

        try:
            for path in root.rglob("*"):
                # Skip virtual envs, git, and log files
                parts = path.parts
                if any(ignored in parts for ignored in (".venv", ".git", "__pycache__")):
                    continue
                if path.name == ".env":
                    continue

                if path.is_file():
                    if ext_filter and not path.suffix.lower() == ext_filter:
                        continue
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            for line_no, line in enumerate(f, start=1):
                                if query_clean in line.lower():
                                    rel_path = path.relative_to(root)
                                    matches.append(f"{rel_path}:{line_no} -> {line.strip()[:100]}")
                                    if len(matches) >= 25:
                                        break
                    except Exception:
                        continue
                if len(matches) >= 25:
                    break

            if not matches:
                return f"No matches found for '{query}'."

            header = f"Found {len(matches)} match(es) for '{query}':\n"
            return header + "\n".join(matches)
        except Exception as e:
            return f"Search error: {e}"
