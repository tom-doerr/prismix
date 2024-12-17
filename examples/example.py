"""
Example script demonstrating the usage of the IterativeProgrammer from Prismix.
"""

from prismix.core.iterative_programmer import setup_agent


def main():
    """
    Main function to demonstrate the usage of the IterativeProgrammer.
    """
    programmer = setup_agent()
    result = programmer.forward(
        "Create a function that calculates factorial of a number"
    )
    print("Generated Code:")
    print(result.code)
    print("\nExecution Result:")
    print(result.output)

    # Test the generated factorial function
    if result.success:
        # Get access to the defined function
        # Safer execution using CodeExecutor
        wrapped_code = f"""def main():
        {result.code.replace('```python', '').replace('```', '').strip().replace(r'\n', '\n    ')}
    main()"""
        code_result = CodeExecutor.execute(wrapped_code)
        assert code_result.success, f"Code execution failed: {code_result.error}"
        factorial = locals().get("factorial") or locals().get("main")

        # Test cases
        test_cases = [0, 1, 5]
        print("\nTesting factorial function:")
        for n in test_cases:
            print(f"factorial({n}) = {factorial(n)}")

    if result.error:
        print("\nErrors:")
        print(result.error)


if __name__ == "__main__":
    main()
