import subprocess
import sys

def run_ruff_and_fix():
    """Runs ruff to lint and fix code style issues."""
    try:
        subprocess.run(["ruff", "."], check=True)
        subprocess.run(["ruff", ".", "--fix"], check=True)
        subprocess.run(["pylint", "."], check=True)
        # Run the script and capture any errors
        subprocess.run([sys.executable, "."], check=True)
        print("Ruff and Pylint checks and fixes applied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running ruff or pylint: {e}")

if __name__ == "__main__":
    run_ruff_and_fix()
