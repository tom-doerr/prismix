from iterative_programmer import setup_agent

def main():
    programmer = setup_agent()
    result = programmer.forward("Create a function that calculates factorial of a number")
    print("Generated Code:")
    print(result.code)
    print("\nExecution Result:")
    print(result.output)
    if result.error:
        print("\nErrors:")
        print(result.error)

if __name__ == "__main__":
    main()
