from typing import List, Dict, Union

def add_numbers(numbers: List[float]) -> float:
    """Add all numbers in the list."""
    return sum(numbers)

def multiply_numbers(numbers: List[float]) -> float:
    """Multiply all numbers in the list."""
    result = 1
    for num in numbers:
        result *= num
    return result

def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of the numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def calculate_stats(numbers: List[float]) -> Dict[str, float]:
    """Calculate the minimum, maximum, and average of the numbers."""
    if not numbers:
        return {"min": 0, "max": 0, "avg": 0}
    total = sum(numbers)
    minimum = min(numbers)
    maximum = max(numbers)
    return {
        "min": minimum,
        "max": maximum,
        "avg": total / len(numbers)
    }

def process_calculation(operation: str, numbers: List[float]) -> Union[float, Dict[str, float], None]:
    """Process the calculation based on the operation."""
    operations = {
        "add": add_numbers,
        "multiply": multiply_numbers,
        "average": calculate_average,
        "stats": calculate_stats,
    }
    return operations.get(operation, lambda _: None)(numbers)


def main():
    """Main function to demonstrate process_calculation."""
    numbers = [1, 2, 3, 4, 5]
    print(f"Sum: {process_calculation('add', numbers)}")
    print(f"Product: {process_calculation('multiply', numbers)}")
    print(f"Average: {process_calculation('average', numbers)}")
    print(f"Stats: {process_calculation('stats', numbers)}")


if __name__ == "__main__":
    main()
