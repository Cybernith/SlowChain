# SlowChain by soroosh morshedi
https://sorooshmorshedi.ir

A tiny educational blockchain implementation built with **Python** and **Flask**.

This project is a minimal demo of:

- Basic blockchain data structure
- Simple Proof-of-Work (PoW)
- Transaction handling
- Node registration
- Naive consensus (longest valid chain wins)
- ✅ Digital signatures for transactions (ECDSA)
- 🧪 Unit tests and end-to-end tests with **pytest**

---

## Features

- ⛏️ Mine new blocks with a simple PoW algorithm  
- 💸 Create **signed** transactions between addresses  
- 🌐 Register multiple nodes and reach consensus  
- ✅ Validate the integrity of the chain **and signatures** via code  
- 🔍 Inspect pending transactions, nodes, and the full chain  
- 🧪 Run unit tests for core blockchain logic and E2E tests for the HTTP API

---

## Installation

```bash
git clone <your-repo-url>
cd slowchain

python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## Running a Node

```bash
python app.py 5000
```

If no port is given, it will default to `5000`.

You can run multiple nodes on different ports, for example:

```bash
python app.py 5000
python app.py 5001
python app.py 5002
```

---

## API Endpoints

### 1. Root

**GET /**

Simple hello message.

---

### 2. Get Full Chain

**GET /chain**

Returns the whole blockchain.

**Response example:**

```json
{
  "chain": [...],
  "len_of_chain": 1
}
```

---

### 3. Validate Chain

**GET /chain/validate**

Checks if the current chain is valid.

```json
{
  "message": "Current chain is valid",
  "valid": true
}
```

---

### 4. Create Signed Transaction

**POST /transactions/new**

Transactions must be **digitally signed** (except mining reward transactions which are created internally by the node).

**Body:**

```json
{
  "sender": "sender_address",
  "recipient": "receiver_address",
  "amount": 10,
  "public_key": "hex-encoded-public-key",
  "signature": "hex-encoded-signature"
}
```

- `sender` is an **address** derived from the public key.
- `public_key` is the raw ECDSA public key (secp256k1) encoded as hex.
- `signature` is the hex-encoded ECDSA signature of the message:

```text
"{sender}:{recipient}:{amount}"
```

**Response:**

```json
{
  "message": "Transaction will be added to block 2",
  "pending_transactions": [...]
}
```

If signature or public key is invalid, the API returns `400` with an error message.

---

### 5. List Pending Transactions

**GET /transactions/pending**

Shows all transactions waiting to be mined into a block.

---

### 6. Mine a New Block

**GET /mine**

- Runs the proof-of-work algorithm.
- Rewards the miner with `SlowChain.MINING_REWARD` coins from `"0"` (system).
- Creates and appends a new block to the chain.

Reward transactions are **system-generated** and do not require a signature.

**Response example:**

```json
{
  "message": "New block created on blockchain",
  "pk": 2,
  "node_id": "<this-node-uuid>",
  "transactions": [...],
  "proof_of_work": 12345,
  "previous_hash": "abc123...",
  "len_of_chain": 2
}
```

---

### 7. Register Nodes

**POST /nodes/register**

Register other nodes so this node can participate in consensus.

**Body:**

```json
{
  "nodes": [
    "http://127.0.0.1:5001",
    "127.0.0.1:5002"
  ]
}
```

**Response:**

```json
{
  "message": "Nodes registered successfully",
  "nodes": [
    "127.0.0.1:5001",
    "127.0.0.1:5002"
  ]
}
```

---

### 8. List Nodes

**GET /nodes**

Returns all known nodes.

---

### 9. Resolve Conflicts (Consensus)

**GET /nodes/resolve**

- Fetches `/chain` from all registered nodes.
- If a longer valid chain is found, this node replaces its own chain.

**Response when replaced:**

```json
{
  "message": "Our chain was replaced by a longer valid chain",
  "new_chain": [...]
}
```

**Response when kept:**

```json
{
  "message": "Our chain is authoritative",
  "chain": [...]
}
```

---

## Digital Signatures & Security

SlowChain uses **ECDSA (secp256k1)** to secure transactions.

### Address model

- A key pair is generated using ECDSA.
- The **public key** (raw bytes) is encoded as hex and sent in each transaction.
- The **address** is derived from the public key:

```text
address = sha256(public_key_bytes).hexdigest()[:40]
```

- `sender` must equal this derived address.
- Each transaction includes:
  - `from` (address)
  - `to` (address)
  - `amount`
  - `public_key` (hex)
  - `signature` (hex)

During validation:

1. The address derived from `public_key` must match `from`.
2. The ECDSA `signature` must match the message:

```text
"{from}:{to}:{amount}"
```

3. If any of these checks fail in any block, the whole chain is considered **invalid**.

Mining reward transactions with `from = "0"` are trusted by definition and skip signature validation.

---

### Example: signing a transaction in Python

```python
import ecdsa
import hashlib
import requests

SENDER_PRIVATE_KEY = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
SENDER_PUBLIC_KEY = SENDER_PRIVATE_KEY.get_verifying_key()

public_key_bytes = SENDER_PUBLIC_KEY.to_string()
public_key_hex = public_key_bytes.hex()

# Derive the address from the public key
address = hashlib.sha256(public_key_bytes).hexdigest()[:40]

recipient = "some-recipient-address"
amount = 10

message = f"{address}:{recipient}:{amount}"
signature_bytes = SENDER_PRIVATE_KEY.sign(message.encode())
signature_hex = signature_bytes.hex()

payload = {
    "sender": address,
    "recipient": recipient,
    "amount": amount,
    "public_key": public_key_hex,
    "signature": signature_hex,
}

resp = requests.post("http://127.0.0.1:5000/transactions/new", json=payload)
print(resp.status_code, resp.json())
```

---

## Testing

This project uses **pytest** for both unit tests and end-to-end (E2E) tests.

### Install pytest

If you installed from `requirements.txt`, `pytest` should already be available.  
Otherwise:

```bash
pip install pytest
```

### Run all tests

From the project root:

```bash
pytest
```

### Test structure

- `tests/test_block_chain_unit.py`
  - Tests core `SlowChain` logic:
    - Genesis block creation
    - Signed transactions
    - Proof-of-work
    - Chain validation (valid vs tampered chain, including signature checking)
- `tests/test_app_e2e.py`
  - Uses Flask's test client to hit real HTTP endpoints:
    - `/chain`
    - `/transactions/new`
    - `/mine`

---

## Difficulty & Mining Reward

- Difficulty (leading zeros) is set in `SlowChain.validate_pow()` and `SlowChain.proof_of_work()`.
- Mining reward is configured via `SlowChain.MINING_REWARD`.

You can tweak these values for experiments.

---

## License

This project is licensed under the MIT License.  
See the `LICENSE` file for details.
