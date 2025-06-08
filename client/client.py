from pathlib import Path
import sys, uuid, json
from phe import paillier
import os, hashlib
from phe import paillier
import requests
from random import SystemRandom




# ─────────────────────────────────────────────────────────────────────
# STEP 1.1: Hardcoded Voter Registry & Authentication
# ─────────────────────────────────────────────────────────────────────
REGISTERED_VOTERS = {
    "voter001": {"name": "Alice",   "pin": "alice123"},
    "voter002": {"name": "Bob",     "pin": "bob456"},
    "voter003": {"name": "Charlie", "pin": "charlie789"}
}

def authenticate_voter(voter_id: str, pin: str) -> bool:
    """Return True if the given voter_id and pin match a registered voter."""
    voter = REGISTERED_VOTERS.get(voter_id)
    return (voter is not None) and (voter["pin"] == pin)

# ─────────────────────────────────────────────────────────────────────
# STEP 1.2: Ask the user for vote input ("yes"/"no") and return 1 or 0
# ─────────────────────────────────────────────────────────────────────
def get_vote_input():
    while True:
        vote = input("Vote (yes/no): ").strip().lower()
        if vote in ("yes", "no"):
            return 1 if vote == "yes" else 0
        print("Please type 'yes' or 'no'.")


if __name__ == "__main__":
    # ─────────────────────────────────────────────────────────────────
    # STEP 0 (already executed at import): pubkey, privkey = generate_paillier_keypair()
    # STEP 0.2 (already executed at import): sent pubkey to /set_public_key
    # ─────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────
    # STEP 0.1: Generate Paillier keypair on the kiosk
    # ─────────────────────────────────────────────────────────────────────
    pubkey, privkey = paillier.generate_paillier_keypair()
    print("🔑 Generated new Paillier keypair on client.")

    # ─────────────────────────────────────────────────────────────────────
    # STEP 0.2: Immediately send pubkey to server so it can accept encrypted votes
    # ─────────────────────────────────────────────────────────────────────
    pub_payload = {"n": str(pubkey.n)}
    try:
        r = requests.post("http://localhost:5000/set_public_key", json=pub_payload)
        if r.status_code == 200:
            print("✅ Public key registered with server.")
        else:
            print("❌ Server returned", r.status_code, "when registering public key.")
            sys.exit(1)
    except Exception as e:
        print("❌ Failed to register public key:", e)
        sys.exit(1)

    # ─────────────────────────────────────────────────────────────────────
    # STEP 1: Loop over all hard-coded voters
    # ─────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────
    # STEP 1.1: Authentication
    # ─────────────────────────────────────────────────────────────────
    for voter_id, info in REGISTERED_VOTERS.items():
        print("=== Voter Authentication ===")
        voter_id = input("Enter your Voter ID: ").strip()
        pin      = input("Enter your PIN: ").strip()
        if not authenticate_voter(voter_id, pin):
            print("❌ Invalid Voter ID or PIN. Exiting.")
            sys.exit(1)
        print(f"✅ Voter '{voter_id}' authenticated successfully.\n")

        # ─────────────────────────────────────────────────────────────────
        # STEP 1.2: Get and map vote
        # ─────────────────────────────────────────────────────────────────
        vote_int = get_vote_input()
        print(f"✅ You entered '{'yes' if vote_int else 'no'}' → mapped to {vote_int}.")

        # ─────────────────────────────────────────────────────────────────
        # STEP 1.3: Encrypt the vote under the freshly generated pubkey
        # ─────────────────────────────────────────────────────────────────
        sysrand = SystemRandom()
        enc_vote    = pubkey.encrypt(vote_int)
        ciphertext  = enc_vote.ciphertext()
        exponent    = enc_vote.exponent

        # Build a unique ID for this vote (used on disk and/or server logs)
        vote_id_uuid = uuid.uuid4().hex

        # Create a JSON payload including voter_id, so the server knows who cast it
        vote_payload = {
            "voter_id":   voter_id,                  # <-- include voter_id in payload
            "ciphertext": str(ciphertext),
            "exponent":   exponent
        }

        # ─────────────────────────────────────────────────────────────────
        # STEP 1.4: Write encrypted vote locally (optional backup)
        # ─────────────────────────────────────────────────────────────────
        votes_dir = Path(__file__).parent.parent / "votes"
        votes_dir.mkdir(exist_ok=True)
        vote_file_path = votes_dir / f"{vote_id_uuid}.json"
        with open(vote_file_path, "w") as f:
            json.dump(vote_payload, f)
        print(f"✅ Encrypted vote saved locally to votes/{vote_file_path.name}")

    # ─────────────────────────────────────────────────────────────────
    # STEP 1.5: Immediately POST encrypted vote to server
    # ─────────────────────────────────────────────────────────────────
        try:
            resp = requests.post(
                "http://localhost:5000/submit_vote",  # adjust URL if needed
                json=vote_payload
            )
            if resp.status_code == 200:
                print("✅ Encrypted vote SENT to server (POST /submit_vote).")
            else:
                print(f"❌ Server returned {resp.status_code} when sending vote.")
                print("    Response body:", resp.text)
                sys.exit(1)
        except Exception as e:
            print("❌ Failed to send vote to server:", e)
            sys.exit(1)

        # ─────────────────────────────────────────────────────────────────
        # STEP 1.6: Generate commitment (ZKP) and save locally
        # ─────────────────────────────────────────────────────────────────
        salt = os.urandom(16).hex()
        commitment = hashlib.sha256(f"{vote_int}{salt}".encode()).hexdigest()

        commit_dir = Path(__file__).parent.parent / "commitments"
        commit_dir.mkdir(exist_ok=True)
        commit_file_path = commit_dir / f"{vote_id_uuid}_commit.json"
        with open(commit_file_path, "w") as f:
            json.dump({
                "voter_id":   voter_id,        # <-- include voter_id in payload
                "commitment": commitment,
                "salt":       salt
            }, f)
        print(f"✅ Commitment saved locally to commitments/{commit_file_path.name}")

        # ─────────────────────────────────────────────────────────────────
        # STEP 1.7: Immediately POST commitment to server
        # ─────────────────────────────────────────────────────────────────
        commit_payload = {
            "voter_id":   voter_id,
            "commitment": commitment,
            "salt":       salt
        }
        try:
            resp2 = requests.post(
                "http://localhost:5000/submit_commitment",  # adjust URL if needed
                json=commit_payload
            )
            if resp2.status_code == 200:
                print("✅ Commitment SENT to server (POST /submit_commitment).")
            else:
                print(f"❌ Server returned {resp2.status_code} when sending commitment.")
                print("    Response body:", resp2.text)
                sys.exit(1)
        except Exception as e:
            print("❌ Failed to send commitment to server:", e)
            sys.exit(1)

        # ─────────────────────────────────────────────────────────────────
        # STEP 1.8: Clear sensitive variables from memory
        # ─────────────────────────────────────────────────────────────────
        vote_int       = None
        ciphertext     = None
        exponent       = None
        salt           = None
        commitment     = None
        vote_payload   = None
        commit_payload = None
        enc_vote       = None

        print(f"✅ Completed processing for voter '{voter_id}'.\n")

    # ───────────────────────────────────────────────────────────────────────────
    # STEP 3: Request the encrypted tally from server and decrypt it locally,
    # including counting “No” votes and determining the majority.
    # ───────────────────────────────────────────────────────────────────────────
    print("=== All voters done. Requesting encrypted tally from server. ===")
    try:
        # 3.1: Fetch the encrypted sum (ciphertext + exponent) via HTTP GET
        resp = requests.get("http://localhost:5000/get_encrypted_tally")
        if resp.status_code != 200:
            print("❌ Error retrieving tally:", resp.text)
            sys.exit(1)

        data = resp.json()
        # data should look like: { "ciphertext": "<big-int-string>", "exponent": <int> }
        ct_sum = int(data["ciphertext"])
        exp_sum = int(data["exponent"])

        # 3.2: Reconstruct the EncryptedNumber under the same pubkey
        encrypted_sum = paillier.EncryptedNumber(pubkey, ct_sum, exp_sum)

        # 3.3: Decrypt the sum with the private key → total number of “Yes” votes
        total_yes = privkey.decrypt(encrypted_sum)

        # 3.4: Compute total number of voters and the number of “No” votes
        total_voters = len(REGISTERED_VOTERS)
        total_no = total_voters - total_yes

        # 3.5: Print both counts and indicate which side has the majority
        print(f"🗳️ Final tally: Yes = {total_yes}, No = {total_no}  (out of {total_voters} voters)")
        if total_yes > total_no:
            print("🏆 Outcome: Majority chose 'Yes'.")
        elif total_no > total_yes:
            print("🏆 Outcome: Majority chose 'No'.")
        else:
            print("🏆 Outcome: It's a tie.")
    except Exception as e:
        print("❌ Failed to get or decrypt final tally:", e)
        sys.exit(1)

