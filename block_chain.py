import json
import hashlib
from time import time
from urllib.parse import urlparse

import requests


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
        """
        Create a new block (but do NOT add it to the chain yet).
        """
        block = {
            'pk': len(self.chain) + 1,
            'date_time': time(),
            'transactions': self.transactions.copy(),
            'proof_of_work': proof,
            'previous_hash': previous_hash or self.to_hash(self.chain[-1]),
        }
        return block

    def add_block_to_chain(self, block):
        """
        Add a block to the chain and reset the current list of transactions.
        """
        self.transactions = []
        self.chain.append(block)

    def add_transaction(self, sender, receiver, amount):
        """
        Add a new transaction to the list of pending transactions.

        Returns the index of the block that will hold this transaction.
        """
        self.transactions.append({
            'from': sender,
            'to': receiver,
            'amount': amount,
        })

        return self.previous_block['pk'] + 1

    def validate_pow(self, first_pow, second_pow, difficulty=4):
        """
        Validate a proof-of-work solution.
        Difficulty is the number of leading zeros required.
        """
        proof = f"{first_pow}{second_pow}".encode()
        hash_of_pow = self.sha256(proof)
        return hash_of_pow[:difficulty] == "0" * difficulty

    def proof_of_work(self, previous_pow, difficulty=4):
        """
        Very simple proof-of-work algorithm:
        - Find a number 'proof' such that hash(previous_pow, proof)
          has 'difficulty' leading zeros.
        """
        proof = 0
        # Keep searching while NOT valid
        while not self.validate_pow(previous_pow, proof, difficulty=difficulty):
            proof += 1
        return proof

    def to_hash(self, value):
        """
        Generate a SHA-256 hash of a Python object using JSON serialization.
        """
        input_str = json.dumps(value, sort_keys=True).encode()
        return self.sha256(input_str)

    @staticmethod
    def sha256(sha_input):
        return hashlib.sha256(sha_input).hexdigest()

    def register_node(self, address):
        """
        Add a new node to the list of nodes.

        Expected address formats:
        - "http://127.0.0.1:5000"
        - "https://example.com"
        - "127.0.0.1:5000"
        """
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

            previous_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Consensus algorithm: replace our chain with the longest valid one
        in the network of registered nodes.
        """
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
