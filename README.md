# Confidential Voting System

A CLI-based demonstration of a privacy-preserving voting system using Paillier homomorphic encryption and zero-knowledge–style commitments. Voters cast “yes/no” ballots, which are encrypted and stored so that the server can only tally the sum without ever seeing individual votes. Voters also generate a commitment to their vote (SHA-256 hash of vote+salt) so that the server can later verify, without revealing the vote itself, that each voter indeed knows what they cast.

## 📝 Project Overview

This project implements a two-phase voting protocol:

1. **Phase 1 – Voting & Tally**  
   - **Client**:  
     - Prompts each voter for “yes”/“no.”  
     - Encrypts the vote with a Paillier public key and writes it to `votes/<vote_id>.json`.  
     - Computes a SHA-256 commitment of (`vote_int` ∥ `salt`) → saves to `commitments/<vote_id>_commit.json`.  
   - **Server**:  
     - Reads all encrypted ballots in `votes/` and homomorphically sums them into a single ciphertext.  
     - Decrypts only the total (“yes” count) with the Paillier private key and prints “Yes” vs. “No” tallies.

2. **Phase 2 – Vote Verification**  
   - **Client** (single-voter tool):  
     - Prompts the user to re-enter their vote and the original salt.  
     - Recomputes `SHA-256(vote_int ∥ salt)` and compares to the stored commitment (`commitments/<vote_id>_commit.json`).  
     - Prints “Proof passed” or “Proof failed” (never reveals the vote to anyone else).  
   - **Server** (batch-verification):  
     - Iterates through every `_commit.json` in `commitments/`.  
     - For each `vote_id`, prompts an operator to ask the voter for their “yes/no” and salt, then runs the same hash check and reports “PASSED” or “FAILED” for each.

---

## 📦 Prerequisites

- **Python 3.8+**  
- **pip** (Python package installer)  
- (Optional) **git** for version control  
- **Virtual environment** (highly recommended)

