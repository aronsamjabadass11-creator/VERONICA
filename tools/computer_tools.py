"""
computer_tools.py - Safe computer actions for VERONICA.
"""

import os
import subprocess
import webbrowser
from pathlib import Path

from tools.base import BaseTool


class OpenWebsiteTool(BaseTool):
    name = "open_website"

    description = (
        "Opens a website in the user's default web browser. "
        "Use only when the user explicitly asks to open a website."
    )

    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The website URL to open."
            }
        },
        "required": ["url"]
    }

    def execute(self, **kwargs) -> str:
        url = kwargs.get("url", "").strip()

        if not url:
            return "Error: No website URL was provided."

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            webbrowser.open(url)
            return f"Opened website: {url}"
        except Exception as e:
            return f"Unable to open website: {e}"


class OpenFolderTool(BaseTool):
    name = "open_folder"

    description = (
        "Opens a folder in Windows File Explorer. "
        "Use only for folders the user explicitly asks to open."
    )

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path of the folder to open."
            }
        },
        "required": ["path"]
    }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path", "").strip()

        if not path:
            return "Error: No folder path was provided."

        folder = Path(path).expanduser().resolve()

        if not folder.exists():
            return f"Folder does not exist: {folder}"

        if not folder.is_dir():
            return f"Path is not a folder: {folder}"

        try:
            os.startfile(str(folder))
            return f"Opened folder: {folder}"
        except Exception as e:
            return f"Unable to open folder: {e}"


class OpenApplicationTool(BaseTool):
    name = "open_application"

    description = (
        "Opens one of a small predefined set of safe Windows applications. "
        "Currently supported applications are notepad, calculator, and paint."
    )

    parameters = {
        "type": "object",
        "properties": {
            "application": {
                "type": "string",
                "description": (
                    "Application to open: notepad, calculator, or paint."
                )
            }
        },
        "required": ["application"]
    }

    ALLOWED_APPS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
    }

    def execute(self, **kwargs) -> str:
        application = kwargs.get("application", "").strip().lower()

        if application not in self.ALLOWED_APPS:
            allowed = ", ".join(self.ALLOWED_APPS.keys())
            return (
                f"Application '{application}' is not allowed. "
                f"Allowed applications: {allowed}"
            )

        try:
            subprocess.Popen([self.ALLOWED_APPS[application]])
            return f"Opened {application}."
        except Exception as e:
            return f"Unable to open {application}: {e}"