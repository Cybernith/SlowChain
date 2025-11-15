import copy
from block_chain import SlowChain


def test_genesis_block_created():
    chain = SlowChain()
    assert len(chain.chain) == 1

    genesis = chain.chain[0]
    assert genesis["pk"] == 1
    assert genesis["previous_hash"] == "1"
    assert "proof_of_work" in genesis
    assert "transactions" in genesis
    assert genesis["transactions"] == []


def test_add_transaction_and_pending_list():
    chain = SlowChain()

    index = chain.add_transaction(
        sender="alice",
        receiver="bob",
        amount=10,
    )

    # باید در بلاک بعدی قرار بگیره
    assert index == chain.previous_block["pk"] + 1
    assert len(chain.transactions) == 1
    tx = chain.transactions[0]
    assert tx["from"] == "alice"
    assert tx["to"] == "bob"
    assert tx["amount"] == 10


def test_proof_of_work_valid():
    chain = SlowChain()
    prev_pow = chain.previous_block["proof_of_work"]

    proof = chain.proof_of_work(prev_pow)

    assert chain.validate_pow(prev_pow, proof)


def test_validate_chain_detects_tamper():
    chain = SlowChain()

    chain.add_transaction(sender="alice", receiver="bob", amount=5)

    prev_block = chain.previous_block
    prev_pow = prev_block["proof_of_work"]
    proof = chain.proof_of_work(prev_pow)
    new_block = chain.create_block(proof, chain.to_hash(prev_block))
    chain.add_block_to_chain(new_block)

    good_chain = copy.deepcopy(chain.chain)
    assert chain.validate_chain(good_chain) is True

    bad_chain = copy.deepcopy(chain.chain)
    bad_chain[1]["transactions"][0]["amount"] = 999999

    assert chain.validate_chain(bad_chain) is False
