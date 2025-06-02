import json
import hashlib
import sys
from pathlib import Path

def get_vote_id():
    vote_id = input("Enter your vote ID (the UUID from when you voted): ").strip()
    return vote_id

def load_commitment(vote_id):
    commit_path = Path(__file__).parent.parent / "commitments" / f"{vote_id}_commit.json"
    if not commit_path.exists():
        print(f"Error: Commitment file not found at {commit_path}")
        sys.exit(1)

    try:
        with open(commit_path, "r") as f:
            data = json.load(f)
        stored_commitment = data["commitment"]
        stored_salt       = data["salt"]
    except Exception as e:
        print(f"Error reading commitment file: {e}")
        sys.exit(1)

    return stored_commitment, stored_salt

def get_user_vote_and_salt():
    while True:
        vote = input("Prove your vote → enter 'yes' or 'no': ").strip().lower()
        if vote in ("yes", "no"):
            vote_int = 1 if vote == "yes" else 0
            break
        print("Please type exactly 'yes' or 'no'.")

    salt = input("Enter the salt (hex) from your commitment file: ").strip()
    if not salt:
        print("Error: Salt cannot be empty.")
        sys.exit(1)

    return vote_int, salt

def verify_commitment(stored_commitment, vote_int, salt_hex):
    """
    Recompute hash = SHA256(f"{vote_int}{salt_hex}") and compare to stored_commitment.
    """
    recomputed = hashlib.sha256(f"{vote_int}{salt_hex}".encode()).hexdigest()
    return recomputed == stored_commitment

if __name__ == "__main__":
    # Step 4.1.1: Ask for vote ID
    vote_id = get_vote_id()

    # Step 4.1.2: Load stored commitment and salt
    stored_commitment, stored_salt = load_commitment(vote_id)
    print(f"🔒 Commitment loaded for vote ID {vote_id}.")

    # Step 4.1.3: Ask user to re-enter vote & salt
    vote_int, user_salt = get_user_vote_and_salt()

    # Step 4.1.4: Verify
    if verify_commitment(stored_commitment, vote_int, user_salt):
        print("Proof passed! You have proven knowledge of your vote without disclosing anything else.")
    else:
        print("Proof failed. The vote and salt do not match the stored commitment.")
