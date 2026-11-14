import ast
import math
import operator
import re
from typing import Any, Dict, List, Set, Tuple


_CITATION_PATTERN = re.compile(
    r"\[([^\[\],]+,\s*p\.\s*(\d+))\]",
    flags=re.IGNORECASE,
)
_NUMBER = r"-?\d+(?:\.\d+)?"
_EQUATION_PATTERN = re.compile(
    r"(?P<expression>(?=[0-9.\s()+\-−*/×÷]*[+\-−*/×÷])"
    r"[0-9.\s()+\-−*/×÷]+?)\s*=\s*"
    r"(?P<result>-?\d+(?:\.\d+)?)"
)
_RATIO_FACTORS = {
    "two": 2.0,
    "twice": 2.0,
    "double": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
}
_RATIO_PATTERN = re.compile(
    rf"(?P<left>{_NUMBER})\s+is\s+"
    rf"(?P<factor>{_NUMBER}|{'|'.join(_RATIO_FACTORS)})\s+times\s+"
    rf"(?P<right>{_NUMBER})",
    flags=re.IGNORECASE,
)
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _evaluate_simple_expression(expression: str) -> float:
    normalized = (
        expression.replace("−", "-")
        .replace("×", "*")
        .replace("÷", "/")
    )
    tree = ast.parse(normalized.strip(), mode="eval")
    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](
                evaluate(node.left), evaluate(node.right)
            )
        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        raise ValueError("Unsupported arithmetic expression")

    return evaluate(tree.body)


def arithmetic_is_consistent(answer: str) -> bool:
    """Check simple explicit numeric equations and multiplication claims."""
    for match in _EQUATION_PATTERN.finditer(answer or ""):
        try:
            computed = _evaluate_simple_expression(match.group("expression"))
            if not math.isclose(
                computed,
                float(match.group("result")),
                rel_tol=1e-6,
                abs_tol=1e-8,
            ):
                return False
        except (ArithmeticError, SyntaxError, ValueError):
            return False

    for match in _RATIO_PATTERN.finditer(answer or ""):
        factor_text = match.group("factor").casefold()
        factor = (
            float(factor_text)
            if re.fullmatch(_NUMBER, factor_text)
            else _RATIO_FACTORS[factor_text]
        )
        left = float(match.group("left"))
        right = float(match.group("right"))
        if not math.isclose(left, factor * right, rel_tol=1e-6, abs_tol=1e-8):
            return False
    return True


def citation_errors(answer: str, chunks: List[Dict[str, Any]]) -> List[str]:
    """Return citation validation errors against actual retrieved source pages."""
    available: Set[Tuple[str, int]] = {
        (
            str(chunk.get("document_name", "")).casefold(),
            int(chunk.get("page_number") or 0),
        )
        for chunk in chunks
        if chunk.get("document_name") and chunk.get("page_number") is not None
    }
    citations = list(_CITATION_PATTERN.finditer(answer or ""))
    if not citations:
        return ["No document-and-page citation was found."]

    errors = []
    for citation in citations:
        document_name = citation.group(1).rsplit(",", 1)[0].strip().casefold()
        page_number = int(citation.group(2))
        if (document_name, page_number) not in available:
            errors.append(
                f"Citation does not match retrieved evidence: {citation.group(0)}"
            )
    return errors


def verify_generated_answer(
    answer: str,
    chunks: List[Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    errors = citation_errors(answer, chunks)
    if not arithmetic_is_consistent(answer):
        errors.append("An explicit arithmetic statement failed consistency checks.")
    return not errors, errors
