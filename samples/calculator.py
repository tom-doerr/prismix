def process_calculation(operation, numbers):
    if operation == "add":
        result = 0
        for num in numbers:
            result += num
        return result
    elif operation == "multiply":
        result = 1
        for num in numbers:
            result *= num
        return result
    elif operation == "average":
        if not numbers:
            return 0
        total = 0
        for num in numbers:
            total += num
        return total / len(numbers)
    elif operation == "stats":
        if not numbers:
            return {"min": 0, "max": 0, "avg": 0}
        total = 0
        minimum = numbers[0]
        maximum = numbers[0]
        for num in numbers:
            total += num
            if num < minimum:
                minimum = num
            if num > maximum:
                maximum = num
        return {
            "min": minimum,
            "max": maximum,
            "avg": total / len(numbers)
        }
    else:
        return None

def main():
    numbers = [1, 2, 3, 4, 5]
    print(f"Sum: {process_calculation('add', numbers)}")
    print(f"Product: {process_calculation('multiply', numbers)}")
    print(f"Average: {process_calculation('average', numbers)}")
    print(f"Stats: {process_calculation('stats', numbers)}")

if __name__ == "__main__":
    main()
