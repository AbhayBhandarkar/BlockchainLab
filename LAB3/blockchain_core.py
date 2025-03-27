# blockchain_core.py
# (Identical to the version in the previous answer - contains Block and Blockchain classes)

import hashlib
import datetime
import json
import uuid # Needed if used in transactions

class Block:
    """ Represents a single block in our blockchain. """
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp if isinstance(timestamp, datetime.datetime) else datetime.datetime.now()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash() # Calculate hash immediately

    def calculate_hash(self):
        """ Calculates the SHA-256 hash of the block's contents. """
        try:
            block_string = json.dumps({
                'index': self.index,
                'timestamp': str(self.timestamp),
                'transactions': self.transactions,
                'previous_hash': self.previous_hash,
                'nonce': self.nonce
            }, sort_keys=True).encode()
            return hashlib.sha256(block_string).hexdigest()
        except TypeError as e:
            print(f"Error serializing block for hashing: {e}")
            return "error_hash"

    def __str__(self):
        return (f"Block #{self.index}\n"
                f"Timestamp: {self.timestamp}\n"
                f"Transactions: {json.dumps(self.transactions, indent=2)}\n"
                f"Previous Hash: {self.previous_hash}\n"
                f"Hash: {self.hash}\n"
                f"Nonce: {self.nonce}\n")

class Blockchain:
    """ Manages the chain of blocks FOR A SINGLE NODE. """
    def __init__(self):
        self.chain = []
        self.difficulty = 2
        if not self.chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        if not self.chain:
            genesis_block = Block(
                index=0,
                timestamp=datetime.datetime.now(),
                transactions=[{"type": "genesis", "details": "The beginning"}],
                previous_hash="0"
            )
            genesis_block.hash = genesis_block.calculate_hash()
            self.chain.append(genesis_block)

    def get_latest_block(self):
        return self.chain[-1] if self.chain else None

    def add_block(self, block):
        """ Adds a pre-validated block to the chain. Validation happens in Node. """
        latest_block = self.get_latest_block()
        if latest_block and block.previous_hash == latest_block.hash and block.index == latest_block.index + 1:
            self.chain.append(block)
            return True
        elif not latest_block and block.index == 0:
             self.chain.append(block)
             return True
        else:
            return False

    def is_chain_valid(self, chain_to_validate=None):
        """ Validates a given chain (or self.chain). """
        target_chain = chain_to_validate if chain_to_validate else self.chain
        if not target_chain: return False
        if target_chain[0].index != 0 or target_chain[0].previous_hash != "0": return False
        if target_chain[0].hash != target_chain[0].calculate_hash(): return False
        for i in range(1, len(target_chain)):
            current_block = target_chain[i]
            previous_block = target_chain[i-1]
            if current_block.hash != current_block.calculate_hash(): return False
            if current_block.previous_hash != previous_block.hash: return False
            if current_block.index != previous_block.index + 1: return False
        return True

    def get_patient_history(self, patient_id):
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if isinstance(tx, dict) and tx.get('patient_id') == patient_id:
                    history.append({
                        "block_index": block.index,
                        "timestamp": str(block.timestamp),
                        "transaction": tx
                    })
        return history

    def __str__(self):
        chain_str = f"Blockchain (Length: {len(self.chain)}):\n"
        for block in self.chain:
            chain_str += str(block) + "-" * 20 + "\n"
        return chain_str