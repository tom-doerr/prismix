
if __name__ == "__main__":
    
# samples/basic_function.py

    def calc_sum(a, b):
        """
        Calculate the sum of two numbers.

        Parameters:
        a (int or float): The first number.
        b (int or float): The second number.

        Returns:
        int or float: The sum of a and b.
        """
        result = a + b
        print(f"The sum of {a} and {b} is: {result}")  # Print the result before returning
        return result

    if __name__ == "__main__":
        # Example usage
        calc_sum(3, 5)
        calc_sum(2.5, 4.5)
    main()
