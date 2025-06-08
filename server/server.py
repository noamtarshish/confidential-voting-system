# server/server.py

import sys
from flask import Flask, request, jsonify
from phe import paillier

app = Flask(__name__)

#
# ────────────────────────────────────────────────────────────────────────────
# Global variables on the server
# ────────────────────────────────────────────────────────────────────────────
server_pubkey = None  # Will hold the PaillierPublicKey once set
server_encrypted_sum = None  # Will hold the homomorphic running sum
received_commitments = []  # Simply store all commitments for potential later verification


#
# ────────────────────────────────────────────────────────────────────────────
# Endpoint #1: POST /set_public_key
#   Client sends JSON { "n": "...", "g": "..." }
#   We reconstruct a PaillierPublicKey(n, g) and initialize encrypted_sum = encrypt(0).
# ────────────────────────────────────────────────────────────────────────────
@app.route("/set_public_key", methods=["POST"])
def set_public_key():
    global server_pubkey, server_encrypted_sum

    data = request.get_json()
    # If no JSON or missing "n", return 400:
    if data is None or "n" not in data:
        return jsonify({"error": "Invalid JSON payload; expected 'n'"}), 400

    try:
        n = int(data["n"])
    except ValueError:
        return jsonify({"error": "'n' must be an integer string"}), 400

    # Reconstruct the public key using only n (phe uses g = n + 1 by default):
    server_pubkey = paillier.PaillierPublicKey(n)
    # Initialize running sum as Enc(0) under that public key:
    server_encrypted_sum = server_pubkey.encrypt(0)

    print(f"✅ /set_public_key: Received public key n={n}.")
    print("    Initialized running encrypted sum = Enc(0).")

    return jsonify({"status": "public key stored"}), 200



#
# ────────────────────────────────────────────────────────────────────────────
# Endpoint #2: POST /submit_vote
#   Client sends JSON { "voter_id": "...", "ciphertext": "...", "exponent": 123 }
#   We reconstruct an EncryptedNumber and homomorphically add it to server_encrypted_sum.
# ────────────────────────────────────────────────────────────────────────────
@app.route("/submit_vote", methods=["POST"])
def submit_vote():
    global server_pubkey, server_encrypted_sum

    if server_pubkey is None or server_encrypted_sum is None:
        return jsonify({"error": "Public key has not been set yet"}), 400

    data = request.get_json()
    if data is None or "voter_id" not in data or "ciphertext" not in data or "exponent" not in data:
        return jsonify({"error": "Invalid JSON payload; expected 'voter_id', 'ciphertext', and 'exponent'"}), 400

    try:
        voter_id = data["voter_id"]
        ciphertext = int(data["ciphertext"])
        exponent = int(data["exponent"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid ciphertext/exponent; must be integer strings"}), 400

    # Reconstruct an EncryptedNumber under the stored public key
    try:
        incoming_cipher = paillier.EncryptedNumber(server_pubkey, ciphertext, exponent)
    except Exception as e:
        return jsonify({"error": f"Failed to reconstruct EncryptedNumber: {e}"}), 400

    # Homomorphically add to the running sum
    server_encrypted_sum = server_encrypted_sum + incoming_cipher

    print(f"✅ /submit_vote: Received vote from '{voter_id}'. Added to running sum.")
    return jsonify({"status": "vote recorded"}), 200


#
# ────────────────────────────────────────────────────────────────────────────
# Endpoint #3: POST /submit_commitment
#   Client sends JSON { "voter_id": "...", "commitment": "...", "salt": "..." }
#   We simply store it in memory for potential Phase 2 verification.
# ────────────────────────────────────────────────────────────────────────────
@app.route("/submit_commitment", methods=["POST"])
def submit_commitment():
    global received_commitments

    data = request.get_json()
    if data is None or "voter_id" not in data or "commitment" not in data or "salt" not in data:
        return jsonify({"error": "Invalid JSON payload; expected 'voter_id', 'commitment', and 'salt'"}), 400

    voter_id = data["voter_id"]
    commitment = data["commitment"]
    salt = data["salt"]

    # Store each commitment tuple in memory
    received_commitments.append({
        "voter_id": voter_id,
        "commitment": commitment,
        "salt": salt
    })

    print(f"✅ /submit_commitment: Stored commitment for voter '{voter_id}'.")
    return jsonify({"status": "commitment recorded"}), 200


#
# ────────────────────────────────────────────────────────────────────────────
# Endpoint #4: GET /get_encrypted_tally
#   Returns JSON { "ciphertext": "...", "exponent": 789 } for server_encrypted_sum
# ────────────────────────────────────────────────────────────────────────────
@app.route("/get_encrypted_tally", methods=["GET"])
def get_encrypted_tally():
    global server_pubkey, server_encrypted_sum

    if server_pubkey is None or server_encrypted_sum is None:
        return jsonify({"error": "No votes recorded or public key not set"}), 400

    # Send back the single Ciphertext and exponent
    response = {
        "ciphertext": str(server_encrypted_sum.ciphertext()),
        "exponent": server_encrypted_sum.exponent
    }

    print("✅ /get_encrypted_tally: Returning the current encrypted sum to client.")
    return jsonify(response), 200


#
# ────────────────────────────────────────────────────────────────────────────
# Main entry‐point: start the Flask server
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # You can change host="0.0.0.0" or port=5000 if needed
    print("🚀 Starting server on http://localhost:5000 …")
    app.run(host="0.0.0.0", port=5000)


