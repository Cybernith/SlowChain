# SlowChain by soroosh morshedi
https://sorooshmorshedi.ir

A tiny educational blockchain implementation built with **Python** and **Flask**.

This project is a minimal demo of:

- Basic blockchain data structure
- Simple Proof-of-Work (PoW)
- Transaction handling
- Node registration
- Naive consensus (longest valid chain wins)
- Unit tests and end-to-end tests with **pytest**

---

## Features

- ⛏️ Mine new blocks with a simple PoW algorithm  
- 💸 Create transactions between addresses  
- 🌐 Register multiple nodes and reach consensus  
- ✅ Validate the integrity of the chain via API  
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

### 4. Create Transaction

**POST /transactions/new**

**Body:**

```json
{
  "sender": "address_1",
  "recipient": "address_2",
  "amount": 10
}
```

**Response:**

```json
{
  "message": "Transaction will be added to block 2",
  "pending_transactions": [...]
}
```

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
    - Transactions
    - Proof-of-work
    - Chain validation (valid vs tampered chain)
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
