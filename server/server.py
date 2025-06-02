import pickle
import sys
import json
from pathlib import Path
from phe import paillier

def load_keys():
    base = Path(__file__).parent.parent / "keys"
    pub_path  = base / "pubkey.pkl"
    priv_path = base / "privkey.pkl"

    if not pub_path.exists():
        print(f"❌ Error: public key not found at {pub_path}")
        sys.exit(1)
    if not priv_path.exists():
        print(f"❌ Error: private key not found at {priv_path}")
        sys.exit(1)

    with open(pub_path,  "rb") as f: pubkey  = pickle.load(f)
    with open(priv_path, "rb") as f: privkey = pickle.load(f)
    return pubkey, privkey

def load_encrypted_votes(pubkey):
    votes_dir = Path(__file__).parent.parent / "votes"
    if not votes_dir.exists():
        print(f"❌ Error: votes directory not found at {votes_dir}")
        sys.exit(1)

    files = list(votes_dir.glob("*.json"))
    if not files:
        print(f"❌ No vote files found in {votes_dir}")
        sys.exit(1)

    encrypted_votes = []
    for file in sorted(files):
        try:
            with open(file, "r") as f:
                data = json.load(f)
            ciphertext = int(data["ciphertext"])
            exponent   = data["exponent"]
            enc_vote = paillier.EncryptedNumber(pubkey, ciphertext, exponent)
            encrypted_votes.append(enc_vote)
        except Exception as e:
            print(f"❌ Error parsing {file.name}: {e}")
            sys.exit(1)

    print(f"✅ Loaded {len(encrypted_votes)} encrypted vote(s).")
    return encrypted_votes


def tally_votes(encrypted_votes):
    # 3.3 Homomorphic sum: start from the first vote, then add the rest
    total_enc = encrypted_votes[0]
    for enc in encrypted_votes[1:]:
        total_enc += enc
    print("✅ Homomorphic tally complete.")
    return total_enc

def decrypt_and_display(total_enc, privkey, num_votes):
    # 3.4 Decrypt the homomorphic sum
    total_yes = privkey.decrypt(total_enc)
    total_no  = num_votes - total_yes

    print("✅ Decryption complete.")
    print("Poll results:")
    print(f"  Yes votes: {total_yes}")
    print(f"  No  votes: {total_no}")


if __name__ == "__main__":
    # 3.1 Load keys
    pubkey, privkey = load_keys()
    print("✅ Public & private keys loaded successfully.")

    # 3.2 Discover & parse encrypted votes
    encrypted_votes = load_encrypted_votes(pubkey)
    total_encrypted_vote = tally_votes(encrypted_votes)
    decrypt_and_display(total_encrypted_vote, privkey, len(encrypted_votes))



