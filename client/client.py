import pickle
from pathlib import Path
import sys, uuid, json
from phe import paillier
import os, hashlib



def load_public_key():
    key_path = Path(__file__).parent.parent / "keys" / "pubkey.pkl"
    if not key_path.exists():
        print(f"❌ Error: public key not found at {key_path}")
        sys.exit(1)
    with open(key_path, "rb") as f:
        pubkey = pickle.load(f)
    return pubkey


def get_vote_input():
    while True:
        vote = input("Vote (yes/no): ").strip().lower()
        if vote in ("yes", "no"):
            return 1 if vote == "yes" else 0
        print("Please type 'yes' or 'no'.")


if __name__ == "__main__":
    # 2.1 Load public key
    pubkey = load_public_key()
    print("✅ Public key loaded successfully.")

    # 2.2 Get & map vote
    vote_int = get_vote_input()
    print(f"✅ You entered '{'yes' if vote_int else 'no'}' → mapped to {vote_int}.")

    # ────────────────────────────────
    # 2.3 Encrypt + serialize
    enc_vote = pubkey.encrypt(vote_int)
    # extract the two components needed to reconstruct
    ciphertext = enc_vote.ciphertext()  # big integer
    exponent = enc_vote.exponent  # scaling exponent

    # prepare payload
    vote_id = uuid.uuid4().hex
    payload = {
        "ciphertext": str(ciphertext),
        "exponent": exponent
    }

    # write to votes/<uuid>.json
    votes_dir = Path(__file__).parent.parent / "votes"
    votes_dir.mkdir(exist_ok=True)
    out_path = votes_dir / f"{vote_id}.json"
    with open(out_path, "w") as f:
        json.dump(payload, f)

    print(f"✅ Encrypted vote saved to votes/{out_path.name}")

    # ────────────────────────────────
    # 2.4 Generate & save commitment (ZKP)
    # Create a random 16-byte salt (hex encoded)
    salt = os.urandom(16).hex()
    # Compute SHA256(vote_int || salt)
    commitment = hashlib.sha256(f"{vote_int}{salt}".encode()).hexdigest()

    # Prepare commitment payload
    commit_dir = Path(__file__).parent.parent / "commitments"
    commit_dir.mkdir(exist_ok=True)
    commit_path = commit_dir / f"{vote_id}_commit.json"
    with open(commit_path, "w") as f:
        json.dump({
            "commitment": commitment,
            "salt": salt
        }, f)

    print(f"✅ Commitment saved to commitments/{commit_path.name}")

