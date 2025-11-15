import json
import hashlib
from time import time
from urllib.parse import urlparse

import requests
import ecdsa


class SlowChain:
    MINING_REWARD = 12.5

    def __init__(self) -> None:
        self.chain = []
        self.transactions = []
        self.nodes = set()

        genesis_block = self.create_block(proof=100, previous_hash="1")
        self.add_block_to_chain(genesis_block)

    @property
    def previous_block(self):
        return self.chain[-1]

    def create_block(self, proof, previous_hash=None):
        block = {
            'pk': len(self.chain) + 1,
            'date_time': time(),
            'transactions': self.transactions.copy(),
            'proof_of_work': proof,
            'previous_hash': previous_hash or self.to_hash(self.chain[-1]),
        }
        return block

    def add_block_to_chain(self, block):
        self.transactions = []
        self.chain.append(block)


    @staticmethod
    def tx_message(sender, receiver, amount):
        """Canonical transaction message to be signed."""
        return f"{sender}:{receiver}:{amount}"

    @staticmethod
    def address_from_public_key(public_key_hex: str) -> str:
        public_bytes = bytes.fromhex(public_key_hex)
        return hashlib.sha256(public_bytes).hexdigest()[:40]

    @staticmethod
    def verify_signature(public_key_hex: str, signature_hex: str, message: str) -> bool:
        """
        Verify an ECDSA signature (secp256k1) for the given message.
        """
        try:
            vk = ecdsa.VerifyingKey.from_string(
                bytes.fromhex(public_key_hex),
                curve=ecdsa.SECP256k1
            )
            vk.verify(bytes.fromhex(signature_hex), message.encode())
            return True
        except Exception:
            return False


    def add_transaction(
        self,
        sender,
        receiver,
        amount,
        public_key=None,
        signature=None,
        is_reward=False,
    ):
        if is_reward:
            if sender != "0":
                raise ValueError("Reward transaction must have sender = '0'")
        else:
            if sender == "0":
                raise ValueError("Normal transaction cannot have sender = '0'")

            if not public_key or not signature:
                raise ValueError("public_key and signature are required for non-reward transactions")

            derived_address = self.address_from_public_key(public_key)
            if derived_address != sender:
                raise ValueError("Sender does not match public key")

            msg = self.tx_message(sender, receiver, amount)
            if not self.verify_signature(public_key, signature, msg):
                raise ValueError("Invalid signature for transaction")

        self.transactions.append({
            'from': sender,
            'to': receiver,
            'amount': amount,
            'public_key': public_key,
            'signature': signature,
            'is_reward': is_reward,
        })

        return self.previous_block['pk'] + 1


    def validate_pow(self, first_pow, second_pow, difficulty=4):
        proof = f"{first_pow}{second_pow}".encode()
        hash_of_pow = self.sha256(proof)
        return hash_of_pow[:difficulty] == "0" * difficulty

    def proof_of_work(self, previous_pow, difficulty=4):
        proof = 0
        while not self.validate_pow(previous_pow, proof, difficulty=difficulty):
            proof += 1
        return proof


    def to_hash(self, value):
        input_str = json.dumps(value, sort_keys=True).encode()
        return self.sha256(input_str)

    @staticmethod
    def sha256(sha_input):
        return hashlib.sha256(sha_input).hexdigest()


    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)


    def validate_chain(self, chain):
        if not chain:
            return False

        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            if block['previous_hash'] != self.to_hash(previous_block):
                return False

            if not self.validate_pow(previous_block['proof_of_work'], block['proof_of_work']):
                return False

            for tx in block.get('transactions', []):
                sender = tx.get('from')
                receiver = tx.get('to')
                amount = tx.get('amount')
                public_key = tx.get('public_key')
                signature = tx.get('signature')
                is_reward = tx.get('is_reward', False)

                if is_reward or sender == "0":
                    continue

                if not public_key or not signature:
                    return False

                derived = self.address_from_public_key(public_key)
                if derived != sender:
                    return False

                msg = self.tx_message(sender, receiver, amount)
                if not self.verify_signature(public_key, signature, msg):
                    return False

            previous_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        others = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in others:
            try:
                response = requests.get(f'http://{node}/chain', timeout=5)
            except requests.RequestException:
                continue

            if response.status_code == 200:
                data = response.json()
                length = data.get('len_of_chain')
                chain = data.get('chain')
                if length is None or chain is None:
                    continue

                if length > max_length and self.validate_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False
