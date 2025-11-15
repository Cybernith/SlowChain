import pytest

from app import app, block_chain as global_chain
from block_chain import SlowChain


@pytest.fixture(autouse=True)
def reset_blockchain():
    global_chain.chain = []
    global_chain.transactions = []
    genesis = global_chain.create_block(proof=100, previous_hash="1")
    global_chain.add_block_to_chain(genesis)
    yield


@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as c:
        yield c


def test_get_chain_returns_genesis_block(client):
    resp = client.get("/chain")
    assert resp.status_code == 200

    data = resp.get_json()
    assert "chain" in data
    assert "len_of_chain" in data
    assert data["len_of_chain"] == 1
    assert len(data["chain"]) == 1
    assert data["chain"][0]["pk"] == 1


def test_create_transaction_and_mine_flow(client):
    tx_payload = {
        "sender": "alice",
        "recipient": "bob",
        "amount": 42,
    }
    resp_tx = client.post("/transactions/new", json=tx_payload)
    assert resp_tx.status_code == 201
    data_tx = resp_tx.get_json()
    assert "pending_transactions" in data_tx
    assert len(data_tx["pending_transactions"]) == 1

    resp_mine = client.get("/mine")
    assert resp_mine.status_code == 200
    data_mine = resp_mine.get_json()

    assert data_mine["message"].startswith("New block created")
    assert "pk" in data_mine
    assert "transactions" in data_mine
    assert "proof_of_work" in data_mine
    assert "previous_hash" in data_mine

    resp_chain = client.get("/chain")
    data_chain = resp_chain.get_json()
    assert data_chain["len_of_chain"] >= 2
    assert len(data_chain["chain"]) >= 2

    chain = data_chain["chain"]
    found = False
    for block in chain:
        for tx in block.get("transactions", []):
            if (
                tx.get("from") == "alice"
                and tx.get("to") == "bob"
                and tx.get("amount") == 42
            ):
                found = True
                break
        if found:
            break

    assert found, "Transaction from alice to bob with amount 42 not found in chain"
