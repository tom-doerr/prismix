import sys
import os
from typing import NoReturn
from prismix.core.iterative_programmer import setup_agent

def execute_instruction(instruction: str) -> None:
    """Execute the given instruction using AI."""
    print(f"Executing instruction: {instruction}\n")
    
    print("Initializing AI agent...")
    agent = setup_agent()
    
    print("Generating code...")
    print("-----------------")
    result = agent.forward(instruction)
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    if hasattr(result, 'code'):
        # Handle CodeResult
        import re
        function_match = re.search(r'def\s+(\w+)', result.code)
        function_name = function_match.group(1) if function_match else "generated_code"
        
        output_file = f"output/{function_name}.py"
        os.makedirs("output", exist_ok=True)
        with open(output_file, "w") as f:
            f.write(result.code)
        
        print("\nGeneration Result:")
        print("----------------")
        print("Success:", result.success)
        if result.error:
            print("Error:", result.error)
        if result.output:
            print("\nExecution Output:", result.output)
        print("\nSafety Check:", "PASSED" if result.success else "FAILED")
        print("\nGenerated code saved to:", output_file)
        print("\nContents:")
        print("----------")
        print(result.code)
    else:
        # Handle FileContext
        print("\nFile Edit Result:")
        print("----------------")
        if result.error:
            print("Error:", result.error)
        else:
            print("Changes made:")
            for change in result.changes:
                print(f"- {change}")
            print("\nUpdated file contents:")
            print("---------------------")
            print(result.content)
    print("----------")

def main() -> NoReturn:
    print("CodeWeaver - AI-powered iterative code generation tool")
    
    if len(sys.argv) < 2:
        print("Usage: codeweaver '<instruction>'")
        print("Example: codeweaver 'create a hello world script'")
        return
    
    instruction = sys.argv[1]
    execute_instruction(instruction)

if __name__ == "__main__":
    main()
