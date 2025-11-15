import hashlib
import ecdsa
import pytest

from app import app, block_chain as global_chain
from block_chain import SlowChain


def make_keypair_and_address():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    public_bytes = vk.to_string()
    public_hex = public_bytes.hex()
    address = hashlib.sha256(public_bytes).hexdigest()[:40]
    return sk, public_hex, address


def sign_tx(sk, sender_addr, receiver_addr, amount):
    msg = SlowChain.tx_message(sender_addr, receiver_addr, amount)
    sig = sk.sign(msg.encode())
    return sig.hex()


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


def test_create_signed_transaction_and_mine_flow(client):
    sk, public_hex, address = make_keypair_and_address()
    recipient = "receiver-addr-001"
    amount = 42
    sig_hex = sign_tx(sk, address, recipient, amount)

    tx_payload = {
        "sender": address,
        "recipient": recipient,
        "amount": amount,
        "public_key": public_hex,
        "signature": sig_hex,
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

    resp_chain = client.get("/chain")
    data_chain = resp_chain.get_json()
    chain = data_chain["chain"]
    found = False
    for block in chain:
        for tx in block.get("transactions", []):
            if (
                tx.get("from") == address
                and tx.get("to") == recipient
                and tx.get("amount") == amount
            ):
                found = True
                break
        if found:
            break

    assert found, "Signed transaction not found in chain"
