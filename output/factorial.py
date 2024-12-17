"""
Calculate the factorial of a non-negative integer.
"""


def factorial(n: int) -> int:
    """Calculate the factorial of a non-negative integer."""
    if not isinstance(n, int):
        raise ValueError("Input must be a non-negative integer.")
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0:
        return 1

    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
