import ast
import operator

from agents import function_tool


@function_tool
def calculate_math(expression: str) -> str:
    """
    Safely evaluates a mathematical expression string using AST parsing.

    Uses Python's Abstract Syntax Tree to evaluate only explicit mathematical
    operations, avoiding the severe security risks of built-in eval().

    Args:
        expression (str): A mathematical expression, e.g. "50 * 3 / 2".

    Returns:
        str: The numeric result of the expression, returned as a string.

    Raises:
        TypeError:       If expression is not a string or contains non-numeric constants.
        ValueError:      If expression is empty.
        ZeroDivisionError: If the expression divides by zero.
        SyntaxError:     If the expression cannot be parsed.

    Examples:
        >>> calculate_math("50 * 3 / 2")
        '75.0'
        >>> calculate_math("10 + 2 ** 3")
        '18.0'
        >>> calculate_math("-(4 + 5) * 2")
        '-18.0'
        >>> calculate_math("100 % 3")
        '1.0'
        >>> calculate_math("10 // 3")
        '3.0'
    """

    if not isinstance(expression, str):
        raise TypeError(
            f"Expected a string expression, got {type(expression).__name__}"
        )
    expression = expression.strip()
    if not expression:
        raise ValueError("Expression must not be empty.")

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _evaluate(node: ast.AST) -> float:
        """Recursively walks the AST to evaluate mathematical nodes."""

        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise TypeError(
                    f"Only numeric constants are allowed, got {type(node.value).__name__}"
                )
            return float(node.value)

        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in allowed_operators:
                raise TypeError(
                    f"Unsupported binary operator: {op_type.__name__}"
                )
            left = _evaluate(node.left)
            right = _evaluate(node.right)
            # Explicit zero-division guard
            if op_type is ast.Div and right == 0:
                raise ZeroDivisionError("Division by zero is not allowed.")
            return allowed_operators[op_type](left, right)

        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in allowed_operators:
                raise TypeError(
                    f"Unsupported unary operator: {op_type.__name__}"
                )
            return allowed_operators[op_type](_evaluate(node.operand))

        else:
            raise TypeError(
                f"Unsupported expression component: {ast.dump(node)}"
            )

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise SyntaxError(
            f"Invalid mathematical expression: '{expression}'. Detail: {e}"
        ) from e

    return str(_evaluate(tree.body))
