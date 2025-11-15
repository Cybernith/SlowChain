from uuid import uuid4
import sys

from flask import Flask, jsonify, request

from block_chain import SlowChain

app = Flask(__name__)

node_id = str(uuid4())

block_chain = SlowChain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()

    required_fields = {'sender', 'recipient', 'amount'}
    if not data or not required_fields.issubset(data):
        return jsonify({'error': 'Missing fields. Required: sender, recipient, amount'}), 400

    this_block_index = block_chain.add_transaction(
        sender=data['sender'],
        receiver=data['recipient'],
        amount=data['amount'],
    )
    response = {
        'message': f'Transaction will be added to block {this_block_index}',
        'pending_transactions': block_chain.transactions,
    }
    return jsonify(response), 201


@app.route('/transactions/pending', methods=['GET'])
def pending_transactions():
    return jsonify({
        'pending_transactions': block_chain.transactions,
        'count': len(block_chain.transactions),
    }), 200


@app.route("/")
def hello_world():
    return "<p>hello, this is SlowChain!</p>"


@app.route('/chain', methods=['GET'])
def get_block_chain():
    response = {
        'chain': block_chain.chain,
        'len_of_chain': len(block_chain.chain)
    }
    return jsonify(response), 200


@app.route('/chain/validate', methods=['GET'])
def validate_chain():
    is_valid = block_chain.validate_chain(block_chain.chain)
    status = 'valid' if is_valid else 'invalid'
    response = {
        'message': f'Current chain is {status}',
        'valid': is_valid,
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    previous_block = block_chain.previous_block
    previous_pow = previous_block['proof_of_work']
    proof = block_chain.proof_of_work(previous_pow)

    # Reward for mining a new block
    block_chain.add_transaction(
        sender="0",
        receiver=node_id,
        amount=block_chain.MINING_REWARD
    )

    previous_hash = block_chain.to_hash(previous_block)
    block = block_chain.create_block(proof, previous_hash)
    block_chain.add_block_to_chain(block)

    response = {
        'message': 'New block created on blockchain',
        'pk': block['pk'],
        'node_id': node_id,
        'transactions': block['transactions'],
        'proof_of_work': block['proof_of_work'],
        'previous_hash': block['previous_hash'],
        'len_of_chain': len(block_chain.chain),
    }

    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()
    nodes = values.get('nodes') if values else None

    if nodes is None or not isinstance(nodes, list) or not nodes:
        return jsonify({'error': 'Please supply a JSON body with a non-empty "nodes" list.'}), 400

    for node in nodes:
        block_chain.register_node(node)

    response = {
        'message': 'Nodes registered successfully',
        'nodes': list(block_chain.nodes)
    }
    return jsonify(response), 201


@app.route('/nodes', methods=['GET'])
def list_nodes():
    response = {
        'nodes': list(block_chain.nodes),
        'count': len(block_chain.nodes),
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = block_chain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced by a longer valid chain',
            'new_chain': block_chain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': block_chain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='0.0.0.0', port=port)
