def process_calculation(operation, numbers):
    """Process a calculation based on the operation and numbers provided."""
    if operation == "add":
        return sum(numbers)
    elif operation == "multiply":
        result = 1
        for num in numbers:
            result *= num
        return result
    elif operation == "average":
        if not numbers:
            return 0
        return sum(numbers) / len(numbers)
    elif operation == "stats":
        if not numbers:
            return {"min": 0, "max": 0, "avg": 0}
        return {
            "min": min(numbers),
            "max": max(numbers),
            "avg": sum(numbers) / len(numbers),
        }
    else:
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
