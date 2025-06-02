from phe import paillier

# 1. Generate a keypair
pubkey, privkey = paillier.generate_paillier_keypair()

# 2. Encrypt two sample votes
enc_yes = pubkey.encrypt(1)
enc_no  = pubkey.encrypt(0)

# 3. Homomorphically add them
enc_sum = enc_yes + enc_no

# 4. Decrypt and verify the result
total = privkey.decrypt(enc_sum)
assert total == 1, f"Expected 1, got {total}"

print("Paillier smoke test passed.")
