import copy
import ecdsa

from block_chain import SlowChain


def make_keypair_and_address():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    public_hex = vk.to_string().hex()

    tmp_chain = SlowChain()
    address = tmp_chain.address_from_public_key(public_hex)
    return sk, public_hex, address


def sign_tx(sk, sender_addr, receiver_addr, amount):
    msg = SlowChain.tx_message(sender_addr, receiver_addr, amount)
    sig = sk.sign(msg.encode())
    return sig.hex()


def test_genesis_block_created():
    chain = SlowChain()
    assert len(chain.chain) == 1

    genesis = chain.chain[0]
    assert genesis["pk"] == 1
    assert genesis["previous_hash"] == "1"
    assert "proof_of_work" in genesis
    assert "transactions" in genesis
    assert genesis["transactions"] == []


def test_add_signed_transaction_and_pending_list():
    chain = SlowChain()

    sk, public_hex, address = make_keypair_and_address()
    receiver = "receiver-address-001"
    amount = 10

    sig_hex = sign_tx(sk, address, receiver, amount)

    index = chain.add_transaction(
        sender=address,
        receiver=receiver,
        amount=amount,
        public_key=public_hex,
        signature=sig_hex,
    )

    assert index == chain.previous_block["pk"] + 1
    assert len(chain.transactions) == 1
    tx = chain.transactions[0]
    assert tx["from"] == address
    assert tx["to"] == receiver
    assert tx["amount"] == amount
    assert tx["public_key"] == public_hex
    assert tx["signature"] == sig_hex


def test_proof_of_work_valid():
    chain = SlowChain()
    prev_pow = chain.previous_block["proof_of_work"]

    proof = chain.proof_of_work(prev_pow)

    assert chain.validate_pow(prev_pow, proof)


def test_validate_chain_detects_tamper_in_signed_tx():
    chain = SlowChain()

    sk, public_hex, address = make_keypair_and_address()
    receiver = "receiver"
    amount = 5
    sig_hex = sign_tx(sk, address, receiver, amount)

    chain.add_transaction(
        sender=address,
        receiver=receiver,
        amount=amount,
        public_key=public_hex,
        signature=sig_hex,
    )

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
