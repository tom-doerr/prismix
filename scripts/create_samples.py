"""
Script to create sample files.
"""

from pathlib import Path


def create_sample_files():
    """Create sample Python files for editing practice"""
    # Create samples directory
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)

    # Basic function without docstring
    basic_func = samples_dir / "basic_function.py"
    basic_func.write_text(
        '''
def calculate_sum(a, b):
    return a + b

def main():
    """Main function to execute the sum calculation and print the result."""
    result = calculate_sum(5, 3)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
'''.lstrip()
    )

    # Class needing type hints
    class_file = samples_dir / "user_manager.py"
    class_file.write_text(
        '''
class UserManager:
    """Manages user data."""
    def __init__(self):
        self.users = []
    
    def add_user(self, username, email):
        """Add a user to the manager."""
        if not username or not email:
            return False
        self.users.append({"username": username, "email": email})
        return True
    
    def get_user(self, username):
        """Get a user by username."""
        for user in self.users:
            if user["username"] == username:
                return user
        return None

def main():
    """Main function to demonstrate UserManager."""
    manager = UserManager()
    manager.add_user("alice", "alice@example.com")
    print(manager.get_user("alice"))

if __name__ == "__main__":
    main()
'''.lstrip()
    )

    # File operations without error handling
    file_ops = samples_dir / "file_processor.py"
    file_ops.write_text(
        """
def process_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
        return
    except IOError:
        print(f"Error: An error occurred while reading the file {filepath}.")
        return

    words = content.split()
    word_count = len(words)
    
    try:
        with open(filepath + '.stats', 'w', encoding='utf-8') as f:
            f.write(f"Word count: {word_count}")
    except IOError:
        print(f"Error: An error occurred while writing to the file {filepath + '.stats'}.")

def main():
    process_file("input.txt")

if __name__ == "__main__":
    main()
""".lstrip()
    )

    # Long function needing refactoring
    complex_calc = samples_dir / "calculator.py"
    complex_calc.write_text(
        '''Sample calculator module.

def process_calculation(operation, numbers):
    """Process different types of calculations based on the operation."""
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
    """Main function to demonstrate the calculator."""
    numbers = [1, 2, 3, 4, 5]
    print(f"Sum: {process_calculation('add', numbers)}")
    print(f"Product: {process_calculation('multiply', numbers)}")
    print(f"Average: {process_calculation('average', numbers)}")
    print(f"Stats: {process_calculation('stats', numbers)}")

if __name__ == "__main__":
    main()
'''.lstrip()
    )


if __name__ == "__main__":
    create_sample_files()
