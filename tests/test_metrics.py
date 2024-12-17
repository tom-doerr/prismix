from prismix.core.metrics import (
    calculate_levenshtein_similarity,
    check_indentation_consistency,
    check_formatting,
    evaluate_edit,
)

"""
Test module for metrics calculations.
"""

"""
Test module for metrics calculations.
"""

def test_levenshtein_similarity():
    """Test Levenshtein similarity calculation"""
    # Identical texts
    assert calculate_levenshtein_similarity("hello", "hello") == 1.0
    # Completely different texts
    assert calculate_levenshtein_similarity("hello", "world") < 0.5
    # Similar texts
    assert calculate_levenshtein_similarity("hello", "helo") > 0.7
    # Empty texts
    assert calculate_levenshtein_similarity("", "") == 1.0
    assert calculate_levenshtein_similarity("hello", "") == 0.0
    # Partial match
    assert calculate_levenshtein_similarity("hello", "hell") > 0.7


def test_indentation_consistency():
    """Test indentation consistency checking"""
    # Correct indentation (multiples of 4)
    good_code = ["def hello():", "    print('hi')", "        return True"]
    assert check_indentation_consistency(good_code) == 1.0

    # Mixed indentation
    bad_code = [
        "def hello():",
        "   print('hi')",  # 3 spaces
        "     return True",  # 5 spaces
    ]
    assert check_indentation_consistency(bad_code) < 1.0

    # Empty lines
    code_with_empty = ["def hello():", "", "    print('hi')", "", "    return True"]
    assert check_indentation_consistency(code_with_empty) == 1.0


def test_formatting():
    """Test code formatting checks"""
    # Good formatting
    good_code = """
def calculate(x, y):
    result = x + y
    return result
"""
    assert check_formatting(good_code) == 1.0

    # Bad formatting
    bad_code = """
def calculate(x,y):
    result=x+y
    return result
"""
    assert check_formatting(bad_code) < 1.0


def test_edit_evaluation():
    """Test overall edit evaluation"""
    original = """
def hello():
    print('hi')
    return True
"""

    # Good edit
    good_edit = """
def hello():
    print('hello world')
    return True
"""
    good_metrics = evaluate_edit(original, good_edit)
    assert good_metrics.total_score > 0.8

    # Bad edit (poor formatting)
    bad_edit = """
def hello():
   print('hello world')
  return True
"""
    bad_metrics = evaluate_edit(original, bad_edit)
    assert bad_metrics.total_score < 0.8
