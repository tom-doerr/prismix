
def add_numbers(num1, num2):
    """
    Adds two numbers together.

    Parameters:
    num1 (int or float): The first number to add.
    num2 (int or float): The second number to add.

    Returns:
    float: The sum of num1 and num2 if both are numbers.

    Raises:
    TypeError: If either num1 or num2 is not a number.
    """
    if isinstance(num1, (int, float)) and isinstance(num2, (int, float)):
        return num1 + num2
    else:
        raise TypeError("Both inputs must be numbers (int or float).")
    """
    Adds two numbers together.

    Parameters:
    num1 (int or float): The first number to add.
    num2 (int or float): The second number to add.

    Returns:
    float: The sum of num1 and num2 if both are numbers.

    Raises:
    TypeError: If either num1 or num2 is not a number.
    """
    if isinstance(num1, (int, float)) and isinstance(num2, (int, float)):
        return num1 + num2
    else:
        raise TypeError("Both inputs must be numbers (int or float).")

# Test cases
if __name__ == "__main__":
    print(add_numbers(5, 3))          # Expected output: 8
    print(add_numbers(5.5, 4.5))      # Expected output: 10.0
    print(add_numbers(5, 2.5))        # Expected output: 7.5
    try:
        print(add_numbers(5, "3"))     # Expected to raise TypeError
    except TypeError as e:
        print(e)                      # Output: Both inputs must be numbers (int or float).
    try:
        print(add_numbers("5", 3))     # Expected to raise TypeError
    except TypeError as e:
        print(e)                      # Output: Both inputs must be numbers (int or float).
    main()
