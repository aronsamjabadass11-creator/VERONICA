"""
registry.py - Central registry and dispatcher for all VERONICA tools.
"""

import json
from typing import Dict, Any, List, Optional
from tools.base import BaseTool
from tools.calculator import CalculatorTool
from tools.system_tools import DateTimeTool, ListFilesTool, ReadFileTool, SearchFilesTool
from tools.system_info import SystemInfoTool
from tools.computer_tools import (
    OpenWebsiteTool,
    OpenFolderTool,
    OpenApplicationTool,
)
from tools.web_search import WebSearchTool
from tools.read_webpage import ReadWebpageTool
from config.logging_config import logger



class ToolRegistry:
    """Manages available tools, schema generation, and execution."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def register(self, tool: BaseTool):
        """Registers a tool with the registry."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: '{tool.name}'")

    def _register_default_tools(self):
        """Registers all built-in safe tools."""
        self.register(CalculatorTool())
        self.register(DateTimeTool())
        self.register(ListFilesTool())
        self.register(ReadFileTool())
        self.register(SearchFilesTool())
        self.register(SystemInfoTool())
        self.register(OpenWebsiteTool())
        self.register(OpenFolderTool())
        self.register(OpenApplicationTool())
        self.register(WebSearchTool())
        self.register(ReadWebpageTool())

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Gets a tool by its registered name."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Returns list of registered tool names."""
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Returns the list of tool schemas for Groq API."""
        return [tool.to_groq_schema() for tool in self._tools.values()]

    def execute_tool(self, tool_name: str, arguments: Any) -> str:
        """
        Executes a registered tool by name with arguments.
        Handles JSON string arguments, dictionary arguments, and exceptions.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            logger.warning(f"Tool execution failed: Unknown tool '{tool_name}'")
            return f"Error: Tool '{tool_name}' is not recognized."

        # Parse arguments if passed as JSON string
        kwargs: Dict[str, Any] = {}
        if isinstance(arguments, str):
            try:
                kwargs = json.loads(arguments) if arguments.strip() else {}
            except json.JSONDecodeError as err:
                logger.error(f"Failed to decode arguments for '{tool_name}': {err}")
                return f"Error parsing arguments for tool '{tool_name}': {err}"
        elif isinstance(arguments, dict):
            kwargs = arguments

        try:
            logger.info(f"Executing tool: {tool_name}")
            result = tool.execute(**kwargs)
            return str(result)
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return f"Execution error in tool '{tool_name}': {e}"


# Global default registry instance
default_tool_registry = ToolRegistry()
from tools.computer_tools import (
    OpenWebsiteTool,
    OpenFolderTool,
    OpenApplicationTool,
)