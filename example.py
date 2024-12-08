from codeweaver.core.iterative_programmer import setup_agent

def main():
    programmer = setup_agent()
    result = programmer.forward("Create a function that calculates factorial of a number")
    print("Generated Code:")
    print(result.code)
    print("\nExecution Result:")
    print(result.output)
    
    # Test the generated factorial function
    if result.success:
        # Get access to the defined function
        local_vars = {}
        exec(result.code, {}, local_vars)
        factorial = local_vars['factorial']
        
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
