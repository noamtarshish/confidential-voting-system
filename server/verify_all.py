import json
import hashlib
import sys
from pathlib import Path

def discover_commitments():
    """
    Find all files named <vote_id>_commit.json under ../commitments.
    Return a list of tuples: (vote_id, stored_commitment, stored_salt).
    """
    commit_dir = Path(__file__).parent.parent / "commitments"
    if not commit_dir.exists():
        print(f"❌ Error: commitments directory not found at {commit_dir}")
        sys.exit(1)

    files = list(commit_dir.glob("*_commit.json"))
    if not files:
        print(f"❌ No commitment files found in {commit_dir}")
        sys.exit(1)

    results = []
    for file in sorted(files):
        # Filename is something like "0da34f57521d4f28a6a8be4cd6b1d065_commit.json"
        filename = file.name
        if not filename.endswith("_commit.json"):
            continue
        vote_id = filename[:-len("_commit.json")]

        try:
            with open(file, "r") as f:
                data = json.load(f)
            stored_commitment = data["commitment"]
            stored_salt       = data["salt"]
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            sys.exit(1)

        results.append((vote_id, stored_commitment, stored_salt))
    return results

def prompt_for_vote_and_salt(vote_id):
    """
    Ask the operator to type in:
      1) The voter’s original 'yes' or 'no'
      2) The salt (hex) that was stored
    Returns: (vote_int, salt_hex)
    """
    print(f"\n— Verifying vote ID: {vote_id} —")
    # 1. Prompt for vote
    while True:
        vote = input("  Enter vote (‘yes’ or ‘no’): ").strip().lower()
        if vote in ("yes", "no"):
            vote_int = 1 if vote == "yes" else 0
            break
        print("  Please type exactly 'yes' or 'no'.")
    # 2. Prompt for salt
    salt = input("  Enter salt (hex) from commitment: ").strip()
    if not salt:
        print("  ❌ Error: Salt cannot be empty.")
        sys.exit(1)
    return vote_int, salt

def verify_commitment(stored_commitment, vote_int, salt_hex):
    """
    Recompute SHA256(f"{vote_int}{salt_hex}") and compare to stored_commitment.
    """
    recomputed = hashlib.sha256(f"{vote_int}{salt_hex}".encode()).hexdigest()
    return recomputed == stored_commitment

if __name__ == "__main__":
    # Step 4.2.1: Discover all commitment files
    all_commitments = discover_commitments()
    print(f"✅ Found {len(all_commitments)} commitment file(s) to verify.")

    # Step 4.2.2: For each vote_id, run the prompt & verification
    for vote_id, stored_commitment, stored_salt in all_commitments:
        # We still keep stored_salt here for logging or future use,
        # but we will prompt the operator to re-enter the salt anyway.
        vote_int, user_salt = prompt_for_vote_and_salt(vote_id)

        if verify_commitment(stored_commitment, vote_int, user_salt):
            print(f"  ✅ Proof for {vote_id}: PASSED.\n")
        else:
            print(f"  ❌ Proof for {vote_id}: FAILED.\n")
