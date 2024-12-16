"""
This module provides functions for calculating and evaluating metrics related to code edits.
"""

"""
This module provides functions for calculating and evaluating metrics related to code edits.
"""

from typing import List
from rapidfuzz.distance import Levenshtein
from dataclasses import dataclass


@dataclass
class EditMetrics:
    """Metrics for evaluating file edits"""

    levenshtein_distance: float
    formatting_score: float
    indentation_consistency: float
    total_score: float


def calculate_levenshtein_similarity(text1: str, text2: str) -> float:
    """Calculate normalized Levenshtein similarity between two texts"""
    distance = Levenshtein.distance(text1, text2)
    max_len = max(len(text1), len(text2))
    if max_len == 0:
        return 1.0
    return 1 - (distance / max_len)


def check_indentation_consistency(lines: List[str]) -> float:
    """Check if indentation is consistent (multiples of 4 spaces)"""
    if not lines:
        return 1.0

    scores = []
    for line in lines:
        if line.strip():  # Skip empty lines
            spaces = len(line) - len(line.lstrip())
            scores.append(1.0 if spaces % 4 == 0 else 0.0)

    return sum(scores) / len(scores) if scores else 1.0


def check_formatting(content: str) -> float:
    """Check Python code formatting conventions"""
    lines = content.splitlines()
    scores = []

    for line in lines:
        line_score = 1.0
        # Check operator spacing
        if any(op in line for op in ["=", "+", "-", "*", "/"]):
            if "=" in line and " = " not in line:
                line_score *= 0.8
            if any(op in line and f" {op} " not in line for op in ["+", "-", "*", "/"]):
                line_score *= 0.8
        # Check comma spacing
        if "," in line and ", " not in line:
            line_score *= 0.8
        scores.append(line_score)

    return sum(scores) / len(scores) if scores else 1.0


def evaluate_edit(original: str, edited: str) -> EditMetrics:
    """Evaluate the quality of a file edit"""
    similarity = calculate_levenshtein_similarity(original, edited)
    formatting = check_formatting(edited)
    indentation = check_indentation_consistency(edited.splitlines())

    # Weight the different metrics
    total_score = (
        similarity * 0.4  # Similarity to original
        + formatting * 0.3  # Code formatting
        + indentation * 0.3  # Indentation consistency
    )

    return EditMetrics(
        levenshtein_distance=similarity,
        formatting_score=formatting,
        indentation_consistency=indentation,
        total_score=total_score,
    )
