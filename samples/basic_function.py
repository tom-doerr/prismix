def calculate_sum(a, b, c):  # Updated to include an additional parameter
    """Calculate the sum of two numbers."""
    print(f"The sum is: {a + b + c}")
    return a + b + c

def main():
    """Main function to execute the sum calculation and print the result."""
    result = calculate_sum(5, 3, 0)  # Assuming c should be 0 for this example
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
