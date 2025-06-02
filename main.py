#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run_script(script_path, args=None):
    """
    Helper to run a Python script (in the same venv).
    script_path: Path to the .py file you want to run
    args: an optional list of additional arguments to pass
    """
    if args is None:
        args = []
    try:
        # Use the same Python interpreter that launched this script:
        python_exe = sys.executable
        cmd = [python_exe, str(script_path)] + args
        result = subprocess.run(cmd, capture_output=False)
        # If the script returns a non-zero exit code, propagate it
        if result.returncode != 0:
            print(f"\nScript {script_path.name} exited with code {result.returncode}\n")
        return result.returncode
    except FileNotFoundError:
        print(f"Could not find {script_path}")
        return 1

def generate_keys():
    print("\n=== Generating Paillier keypair ===")
    keygen_script = Path(__file__).parent / "keys" / "keygen_paillier.py"
    return run_script(keygen_script)

def cast_vote():
    print("\n=== Casting a new vote ===")
    client_script = Path(__file__).parent / "client" / "client.py"
    return run_script(client_script)

def tally_votes():
    print("\n=== Tallying votes on server ===")
    server_script = Path(__file__).parent / "server" / "server.py"
    return run_script(server_script)

def verify_all_votes():
    print("\n=== Verifying all commitments ===")
    verify_script = Path(__file__).parent / "server" / "verify_all.py"
    return run_script(verify_script)

def show_menu():
    print("""
=== Confidential Voting System Launcher ===

Please choose an action (enter the number):

  1) Generate Paillier keypair (keys/keygen_paillier.py)
  2) Cast a new vote (client/client.py)
  3) Tally votes (server/server.py)
  4) Verify all commitments (server/verify_all.py)
  5) Exit
""")

if __name__ == "__main__":
    while True:
        show_menu()
        choice = input("Your choice: ").strip()

        if choice == "1":
            rc = generate_keys()
        elif choice == "2":
            rc = cast_vote()
        elif choice == "3":
            rc = tally_votes()
        elif choice == "4":
            rc = verify_all_votes()
        elif choice == "5":
            print("Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
            continue

        # After each action, loop back to menu if rc == 0
        if rc == 0:
            input("\n--- Press ENTER to return to the main menu ---\n")
        else:
            print("\nThere was an error in the last step. Returning to main menu.\n")
            input("--- Press ENTER to continue ---\n")
