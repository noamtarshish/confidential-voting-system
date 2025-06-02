import pickle
from phe import paillier

# 1. Generate a Paillier keypair
pubkey, privkey = paillier.generate_paillier_keypair()

# 2. Save the public key
with open("keys/pubkey.pkl", "wb") as f:
    pickle.dump(pubkey, f)

# 3. Save the private key
with open("keys/privkey.pkl", "wb") as f:
    pickle.dump(privkey, f)

print("Paillier keypair generated and saved in keys/")