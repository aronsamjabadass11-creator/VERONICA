"""
test_tools.py - Unit tests for safe tools and tool registry.
"""

import unittest
from tools.calculator import CalculatorTool
from tools.system_tools import DateTimeTool, ListFilesTool, ReadFileTool, SearchFilesTool
from tools.registry import ToolRegistry


class TestTools(unittest.TestCase):
    """Unit tests for tool functionality and safety."""

    def setUp(self):
        self.calc = CalculatorTool()
        self.dt = DateTimeTool()
        self.reader = ReadFileTool()
        self.lister = ListFilesTool()
        self.searcher = SearchFilesTool()
        self.registry = ToolRegistry()

    def test_calculator_arithmetic(self):
        res = self.calc.execute("25 * 4")
        self.assertIn("100", res)

        res_sqrt = self.calc.execute("sqrt(81) + 1")
        self.assertIn("10", res_sqrt)

    def test_calculator_division_by_zero(self):
        res = self.calc.execute("10 / 0")
        self.assertIn("Division by zero", res)

    def test_calculator_security_blocks_eval(self):
        res = self.calc.execute("__import__('os').system('dir')")
        self.assertIn("Calculation Error", res)

    def test_datetime_tool(self):
        res = self.dt.execute()
        self.assertIn("Current Date:", res)
        self.assertIn("Day of Week:", res)

    def test_file_reading_safety(self):
        # Reading existing safe file
        res = self.reader.execute(file_path="requirements.txt")
        self.assertIn("groq", res)

        # Attempting directory traversal should be blocked
        traversal = self.reader.execute(file_path="../../Windows/System32/drivers/etc/hosts")
        self.assertIn("Security Restriction", traversal)

        # Attempting to read .env should be blocked
        env_attempt = self.reader.execute(file_path=".env")
        self.assertIn("Security Restriction", env_attempt)

    def test_search_files(self):
        res = self.searcher.execute(query="GROQ_API_KEY", file_extension=".py")
        self.assertIn("Found", res)

    def test_registry_dispatch(self):
        res = self.registry.execute_tool("calculator", '{"expression": "7 + 3"}')
        self.assertIn("10", res)


if __name__ == "__main__":
    unittest.main()
