"""Computer Algebra System integration for mathematical operations."""

import random
import re
from typing import Any

import sympy as sp
from sympy import Symbol, simplify, solve, sympify
from sympy.parsing.latex import parse_latex
from sympy.printing.latex import latex

from .schemas import GradingStep


class CASService:
    """Computer Algebra System service using SymPy."""

    def __init__(self) -> None:
        """Initialize the CAS service."""
        self.symbols: dict[str, Symbol] = {}

    def parse_expression(self, expression: str) -> sp.Expr | None:
        """Parse a mathematical expression string into SymPy expression.

        Args:
            expression: Mathematical expression (LaTeX or standard notation)

        Returns:
            SymPy expression or None if parsing fails
        """
        try:
            # Try parsing as LaTeX first
            if "\\" in expression or "{" in expression:
                return parse_latex(expression)

            # Clean up common notation
            cleaned = self._clean_expression(expression)

            # Parse as standard mathematical notation
            return sympify(cleaned)
        except (ValueError, TypeError, SyntaxError):
            return None

    def _clean_expression(self, expression: str) -> str:
        """Clean and normalize mathematical expression.

        Args:
            expression: Raw mathematical expression

        Returns:
            Cleaned expression string
        """
        # Replace common mathematical notation
        cleaned = expression.replace("^", "**")  # Power notation
        cleaned = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", cleaned)  # 2x -> 2*x
        cleaned = re.sub(r"([a-zA-Z])(\d)", r"\1*\2", cleaned)  # x2 -> x*2
        cleaned = re.sub(r"\)(\()", r")*\1", cleaned)  # )(  -> )*(
        cleaned = re.sub(r"(\))([a-zA-Z])", r"\1*\2", cleaned)  # )x -> )*x

        return re.sub(r"([a-zA-Z])(\()", r"\1*\2", cleaned)  # x( -> x*(

    def to_latex(self, expression: sp.Expr) -> str:
        """Convert SymPy expression to LaTeX.

        Args:
            expression: SymPy expression

        Returns:
            LaTeX representation
        """
        return latex(expression)

    def to_ast(self, expression: sp.Expr) -> dict[str, Any]:
        """Convert SymPy expression to AST representation.

        Args:
            expression: SymPy expression

        Returns:
            Abstract syntax tree as dictionary
        """
        return self._expression_to_dict(expression)

    def _expression_to_dict(self, expr: sp.Expr) -> dict[str, Any]:
        """Convert SymPy expression to dictionary representation.

        Args:
            expr: SymPy expression

        Returns:
            Dictionary representation of the expression
        """
        if expr.is_Atom:
            if expr.is_Symbol:
                return {"type": "symbol", "name": str(expr)}
            if expr.is_Number:
                return {"type": "number", "value": float(expr)}
            return {"type": "atom", "value": str(expr)}

        return {
            "type": "operation",
            "operator": type(expr).__name__,
            "args": [self._expression_to_dict(arg) for arg in expr.args],
        }

    def are_equivalent(
        self,
        expr1: sp.Expr,
        expr2: sp.Expr,
        tolerance: float = 1e-6,
    ) -> bool:
        """Check if two expressions are mathematically equivalent.

        Args:
            expr1: First expression
            expr2: Second expression
            tolerance: Numerical tolerance for comparison

        Returns:
            True if expressions are equivalent
        """
        try:
            # Simplify the difference
            diff = simplify(expr1 - expr2)

            # Check if difference is zero
            if diff == 0:
                return True

            # For numerical expressions, check if difference is within
            # tolerance
            if diff.is_number:
                return abs(float(diff)) < tolerance

            # Try substituting random values for symbols
            symbols = diff.free_symbols
            if not symbols:
                return True

            for _ in range(10):  # Test with 10 random values
                # Using random for mathematical equivalence testing
                substitutions = {
                    sym: random.uniform(-10, 10)  # noqa: S311
                    for sym in symbols
                }
                try:
                    val = float(diff.subs(substitutions))
                    if abs(val) > tolerance:
                        return False
                except (ValueError, TypeError):
                    continue

        except (ValueError, TypeError, AttributeError):
            return False
        else:
            return True

    def solve_step_by_step(
        self,
        equation: str,
        variable: str | None = None,
    ) -> list[GradingStep]:
        """Solve equation step by step.

        Args:
            equation: Mathematical equation to solve
            variable: Variable to solve for (if None, auto-detect)

        Returns:
            List of solution steps
        """
        steps: list[GradingStep] = []

        try:
            expr = self.parse_expression(equation)
            if expr is None:
                return steps

            # Add initial step
            steps.append(
                GradingStep(
                    step_number=1,
                    expression=self.to_latex(expr),
                    explanation="Starting with the given equation",
                    rule_applied="Initial state",
                ),
            )

            # Determine variable to solve for
            if variable is None:
                symbols = expr.free_symbols
                if symbols:
                    variable = str(next(iter(symbols)))
                else:
                    return steps

            var_symbol = Symbol(variable)

            # Simplify expression
            simplified = simplify(expr)
            if simplified != expr:
                steps.append(
                    GradingStep(
                        step_number=len(steps) + 1,
                        expression=self.to_latex(simplified),
                        explanation="Simplify the expression",
                        rule_applied="Algebraic simplification",
                    ),
                )

            # Solve the equation
            if "=" in equation:
                # Handle equations (expr = 0 form)
                lhs, rhs = equation.split("=", 1)
                lhs_expr = self.parse_expression(lhs.strip())
                rhs_expr = self.parse_expression(rhs.strip())

                if lhs_expr is not None and rhs_expr is not None:
                    eq = sp.Eq(lhs_expr, rhs_expr)
                    solutions = solve(eq, var_symbol)

                    if solutions:
                        for i, sol in enumerate(solutions):
                            steps.append(
                                GradingStep(
                                    step_number=len(steps) + 1,
                                    expression=(
                                        f"{variable} = {self.to_latex(sol)}"
                                    ),
                                    explanation=f"Solution {i + 1}",
                                    rule_applied="Equation solving",
                                ),
                            )

        except (ValueError, TypeError, NotImplementedError) as e:
            steps.append(
                GradingStep(
                    step_number=len(steps) + 1,
                    expression="Error in computation",
                    explanation=f"Unable to solve: {e!s}",
                    rule_applied="Error handling",
                ),
            )

        return steps

    def evaluate_numerical(
        self,
        expression: sp.Expr,
        substitutions: dict[str, float],
    ) -> float | None:
        """Evaluate expression numerically with given substitutions.

        Args:
            expression: SymPy expression
            substitutions: Variable substitutions

        Returns:
            Numerical result or None if evaluation fails
        """
        try:
            substituted = expression.subs(substitutions)
            return float(substituted)
        except (ValueError, TypeError, AttributeError):
            return None

    def get_expression_complexity(self, expression: sp.Expr) -> int:
        """Calculate complexity score of an expression.

        Args:
            expression: SymPy expression

        Returns:
            Complexity score (higher = more complex)
        """
        try:
            # Count atoms and operations
            return len(expression.atoms()) + len(expression.args)
        except (AttributeError, TypeError):
            return 0


# Global CAS service instance
cas_service = CASService()
