"""
calculator.py - Safe mathematical expression evaluator.
Uses AST traversal to evaluate basic arithmetic without insecure eval().
"""

import ast
import math
import operator
from typing import Dict, Any
from tools.base import BaseTool

# Supported binary operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Supported mathematical functions
SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
}


def _eval_node(node):
    """Recursively evaluate an AST node safely."""
    if isinstance(node, ast.Constant):  # numbers, booleans
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if op_type == ast.Pow and (right > 1000 or left > 10000):
            raise ValueError("Exponent too large to compute safely.")
        return SAFE_OPERATORS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return SAFE_OPERATORS[op_type](operand)

    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only standard mathematical functions are permitted.")
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not in the safe functions list.")
        args = [_eval_node(arg) for arg in node.args]
        func = SAFE_FUNCTIONS[func_name]
        return func(*args)

    elif isinstance(node, ast.Name):
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unknown variable: {node.id}")

    else:
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")


class CalculatorTool(BaseTool):
    """Safe calculator tool for computing math expressions."""

    name = "calculator"
    description = "Safely evaluates a mathematical expression (e.g., '128 * 4', 'sqrt(144) + 10')."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate.",
            }
        },
        "required": ["expression"],
    }

    def execute(self, expression: str = "", **kwargs) -> str:
        """Evaluates the mathematical expression."""
        if not expression or not expression.strip():
            return "Error: Expression cannot be empty."

        clean_expr = expression.strip()
        try:
            tree = ast.parse(clean_expr, mode="eval")
            result = _eval_node(tree.body)
            # Format nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return f"{clean_expr} = {result}"
        except ZeroDivisionError:
            return "Error: Division by zero is undefined."
        except Exception as e:
            return f"Calculation Error: {str(e)}"
