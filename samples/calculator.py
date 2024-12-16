def add_numbers(numbers):
    """Add all numbers in the list."""
    return sum(numbers)

def multiply_numbers(numbers):
    """Multiply all numbers in the list."""
    result = 1
    for num in numbers:
        result *= num
    return result

def calculate_average(numbers):
    """Calculate the average of the numbers."""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def calculate_stats(numbers):
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

def process_calculation(operation, numbers):
    """Process the calculation based on the operation."""
    if operation == "add":
        return add_numbers(numbers)
    if operation == "multiply":
        return multiply_numbers(numbers)
    if operation == "average":
        return calculate_average(numbers)
    if operation == "stats":
        return calculate_stats(numbers)
    return None


def main():
    """Main function to demonstrate process_calculation."""
    numbers = [1, 2, 3, 4, 5]
    print(f"Sum: {process_calculation('add', numbers)}")
    print(f"Product: {process_calculation('multiply', numbers)}")
    print(f"Average: {process_calculation('average', numbers)}")
    print(f"Stats: {process_calculation('stats', numbers)}")


if __name__ == "__main__":
    main()
