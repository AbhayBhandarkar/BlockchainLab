# node_common.py

import socket
import threading
import pickle
import sys
import argparse
import time
import json
import uuid
from datetime import datetime
import traceback
import csv
import os

from blockchain_core import Block, Blockchain

# --- Constants ---
MSG_BUFFER_SIZE = 4096
MSG_HEADER_FORMAT = "!I"
MSG_HEADER_LENGTH = 4

MSG_TYPE_NEW_TRANSACTION = 1
MSG_TYPE_NEW_BLOCK = 2
MSG_TYPE_REQUEST_CHAIN = 3
MSG_TYPE_SEND_CHAIN = 4
MSG_TYPE_REQUEST_PEERS = 5
MSG_TYPE_SEND_PEERS = 6
TX_TRANSFER_ECASH = "TRANSFER_ECASH"
SYSTEM_ACCOUNT = "SYSTEM_BANK_001"
INITIAL_SYSTEM_BALANCE = 1000000

# --- Shared User Management and Balances ---
USERS = {
    "dr_alice": {"password": "password123", "role": "doctor", "name": "Dr. Alice"},
    "lab_tech_bob": {"password": "labpass", "role": "lab", "name": "Bob (Lab)"},
    "pharm_charlie": {"password": "pharmpass", "role": "pharmacy", "name": "Charlie (Pharmacy)"}
}
E_CASH_BALANCES = {user: 0 for user in USERS}
E_CASH_BALANCES[SYSTEM_ACCOUNT] = INITIAL_SYSTEM_BALANCE

# --- CSV File Configuration ---
PATIENT_CSV_FILENAME = "patient_registry.csv"
PATIENT_CSV_HEADER = ['patient_id', 'patient_name', 'registered_by', 'timestamp']

# --- Node Class (Common Logic) ---
class Node:
    def __init__(self, host, port, peers_addr, node_id=None):
        self.host = host
        self.port = port
        self.node_id = node_id if node_id else "{}:{}".format(host, port) # Use format for compatibility
        self.peers = {}
        self.peer_addresses_to_connect = set(peers_addr)
        self.blockchain = Blockchain()
        self.pending_transactions = []
        self.server_socket = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.csv_lock = threading.Lock()
        self.current_user = None

        self._recalculate_all_balances()
        print("Node {} initialized on {}:{}".format(self.node_id, self.host, self.port)) # Use format

    # --- Networking Methods ---
    def start(self):
        if not self._start_server(): return
        listener_thread = threading.Thread(target=self._listen_for_connections, daemon=True)
        listener_thread.start()
        connector_thread = threading.Thread(target=self._connect_to_peers_periodically, daemon=True)
        connector_thread.start()
        sync_thread = threading.Thread(target=self._initial_sync, daemon=True)
        sync_thread.start()
        print("Node {} started. Listening and connecting...".format(self.node_id)) # Use format

    def _start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print("Server listening on {}:{}".format(self.host, self.port)) # Use format
            return True
        except OSError as e: print("!!! Error starting server on {}:{}: {}".format(self.host, self.port, e)); return False # Use format

    def _listen_for_connections(self):
        while not self.stop_event.is_set():
            try:
                self.server_socket.settimeout(1.0)
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(None); self.peers[addr] = client_socket
                handler_thread = threading.Thread(target=self._handle_connection, args=(client_socket, addr), daemon=True); handler_thread.start()
            except socket.timeout: continue
            except OSError as e:
                if not self.stop_event.is_set(): print("[Network] Error accepting connections: {}".format(e)); break # Use format
            except Exception as e:
                if not self.stop_event.is_set(): print("[Network] Unexpected error in listener: {}".format(e)); time.sleep(1) # Use format

    def _connect_to_peers_periodically(self):
        while not self.stop_event.is_set():
            peers_to_try = list(self.peer_addresses_to_connect)
            for peer_host, peer_port in peers_to_try:
                peer_addr = (peer_host, peer_port); is_self = (peer_host == self.host and peer_port == self.port)
                if not is_self and peer_addr not in self.peers: self._connect_to_peer(peer_host, peer_port)
            time.sleep(15)

    def _connect_to_peer(self, peer_host, peer_port):
        peer_addr = (peer_host, peer_port)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.settimeout(5.0); sock.connect(peer_addr)
            sock.settimeout(None); print("[Network] Connected to peer {}:{}".format(peer_host, peer_port)); self.peers[peer_addr] = sock # Use format
            handler_thread = threading.Thread(target=self._handle_connection, args=(sock, peer_addr), daemon=True); handler_thread.start()
        except (socket.timeout, OSError): pass
        except Exception as e:
             if not self.stop_event.is_set(): print("[Network] Unexpected error connecting to {}: {}".format(peer_addr, e)) # Use format

    def _handle_connection(self, client_socket, addr):
        while not self.stop_event.is_set():
            try:
                header = client_socket.recv(MSG_HEADER_LENGTH)
                if not header or len(header) < MSG_HEADER_LENGTH: break
                msg_len = int.from_bytes(header[:MSG_HEADER_LENGTH-1], byteorder='big'); msg_type = int.from_bytes(header[MSG_HEADER_LENGTH-1:], byteorder='big')
                data = b""; bytes_recd = 0
                while bytes_recd < msg_len:
                    chunk = client_socket.recv(min(msg_len - bytes_recd, MSG_BUFFER_SIZE));
                    if not chunk: raise ConnectionAbortedError("Peer disconnected")
                    data += chunk; bytes_recd += len(chunk)
                message = pickle.loads(data); self._process_message(msg_type, message, addr, client_socket)
            except (socket.timeout, ConnectionResetError, ConnectionAbortedError, BrokenPipeError): break
            except pickle.UnpicklingError: print("\n[Network] Invalid data received from peer {}.".format(addr)); continue # Use format
            except OSError: break
            except Exception as e:
                if not self.stop_event.is_set(): print("\n[Network] Unexpected error handling connection with {}: {}".format(addr, e)); traceback.print_exc() # Use format
                break
        if addr in self.peers:
            try: del self.peers[addr]
            except KeyError: pass
        try: client_socket.close()
        except: pass

    def send_message(self, sock, msg_type, data):
        try:
            serialized_data = pickle.dumps(data); msg_len = len(serialized_data)
            header = msg_len.to_bytes(3, byteorder='big') + msg_type.to_bytes(1, byteorder='big')
            sock.sendall(header + serialized_data)
        except (OSError, BrokenPipeError):
            peer_addr = None;
            try: peer_addr = sock.getpeername()
            except: pass
            if peer_addr and peer_addr in self.peers:
                 try: del self.peers[peer_addr]
                 except KeyError: pass
            try: sock.close()
            except: pass
        except Exception as e:
             if not self.stop_event.is_set(): print("[Network] Unexpected error sending message: {}".format(e)) # Use format

    def broadcast(self, msg_type, data, exclude_addr=None):
        peers_to_broadcast = list(self.peers.items())
        for addr, sock in peers_to_broadcast:
            if addr != exclude_addr: self.send_message(sock, msg_type, data)

    def stop(self):
        print("\n--- Stopping Node {} ---".format(self.node_id)); self.stop_event.set() # Use format
        if self.server_socket: self.server_socket.close()
        peers_to_close = list(self.peers.values())
        for sock in peers_to_close:
            try: sock.shutdown(socket.SHUT_RDWR); sock.close()
            except OSError: pass
        print("Node {} stopped.".format(self.node_id)) # Use format

    def _process_message(self, msg_type, data, source_addr, source_sock):
        if msg_type == MSG_TYPE_NEW_TRANSACTION:
            valid_tx = False
            if isinstance(data, dict) and 'type' in data:
                 if data['type'] == TX_TRANSFER_ECASH:
                      if all(k in data for k in ('from', 'to', 'amount')) and isinstance(data['amount'], int) and data['amount'] > 0: valid_tx = True
                 else: valid_tx = True
            if valid_tx:
                with self.lock:
                    tx_repr = json.dumps(data, sort_keys=True)
                    if not any(json.dumps(tx, sort_keys=True) == tx_repr for tx in self.pending_transactions):
                        should_add = True
                        if data['type'] == TX_TRANSFER_ECASH and data['from'] != SYSTEM_ACCOUNT:
                             sender_balance = self.get_current_balance(data['from'])
                             if sender_balance < data['amount']: print("[Warning] Insufficient balance for pending tx from {}. Tx rejected.".format(data['from'])); should_add = False # Use format
                        if should_add: self.pending_transactions.append(data); self.broadcast(MSG_TYPE_NEW_TRANSACTION, data, exclude_addr=source_addr)
            # else: print("[Warning] Invalid transaction data from {}".format(source_addr)) # Use format

        elif msg_type == MSG_TYPE_NEW_BLOCK:
             if isinstance(data, Block):
                latest_block = self.blockchain.get_latest_block();
                if not latest_block and data.index != 0: return
                valid = True; expected_index = 0 if not latest_block else latest_block.index + 1
                if data.index != expected_index: valid = False;
                elif latest_block and data.previous_hash != latest_block.hash: self.request_chain_from_peers(); valid = False
                elif data.hash != data.calculate_hash(): valid = False
                else:
                    temp_balances = self.get_balances_up_to_block(data.previous_hash)
                    for tx in data.transactions:
                         if tx.get('type') == TX_TRANSFER_ECASH:
                              sender, amount = tx.get('from'), tx.get('amount', 0)
                              if sender != SYSTEM_ACCOUNT and temp_balances.get(sender, 0) < amount: print("[Validation] Block {} invalid: Insufficient funds for tx {}".format(data.index, tx)); valid = False; break # Use format
                              temp_balances[sender] = temp_balances.get(sender, 0) - amount; recipient = tx.get('to'); temp_balances[recipient] = temp_balances.get(recipient, 0) + amount
                if valid:
                    block_added = False; generated_tx = []
                    with self.lock:
                        current_latest = self.blockchain.get_latest_block()
                        if (not current_latest and data.index == 0) or \
                           (current_latest and data.previous_hash == current_latest.hash and data.index == current_latest.index + 1):
                             self.blockchain.add_block(data); block_added = True
                             mined_tx_ids = set(json.dumps(tx, sort_keys=True) for tx in data.transactions)
                             self.pending_transactions = [ tx for tx in self.pending_transactions if json.dumps(tx, sort_keys=True) not in mined_tx_ids ]
                             self._update_balances_from_block(data)
                             print("[Node] Block {} added. Balances updated. Pending tx: {}".format(data.index, len(self.pending_transactions))) # Use format
                             generated_tx = self._generate_system_transfers_for_block(data)
                    if block_added:
                        self.broadcast(MSG_TYPE_NEW_BLOCK, data, exclude_addr=source_addr);
                        for sys_tx in generated_tx: self.add_transaction_local(sys_tx)
            # else: print("[Warning] Invalid block data from {}".format(source_addr)) # Use format

        elif msg_type == MSG_TYPE_REQUEST_CHAIN:
            with self.lock: self.send_message(source_sock, MSG_TYPE_SEND_CHAIN, self.blockchain.chain)
        elif msg_type == MSG_TYPE_SEND_CHAIN:
             if isinstance(data, list): self.resolve_conflicts(data)
        elif msg_type == MSG_TYPE_REQUEST_PEERS:
             with self.lock: peer_addr_list = list(self.peers.keys()); self.send_message(source_sock, MSG_TYPE_SEND_PEERS, peer_addr_list)
        elif msg_type == MSG_TYPE_SEND_PEERS:
             if isinstance(data, list):
                  new_peers_found = 0
                  for addr in data:
                       if isinstance(addr, tuple) and len(addr) == 2:
                            is_self = (addr[0] == self.host and addr[1] == self.port)
                            if not is_self and addr not in self.peer_addresses_to_connect and addr not in self.peers: self.peer_addresses_to_connect.add(addr); new_peers_found += 1

    # --- Blockchain Management ---
    def add_transaction_local(self, transaction):
        valid_tx = False
        if isinstance(transaction, dict) and 'type' in transaction:
             if transaction['type'] == TX_TRANSFER_ECASH:
                  if all(k in transaction for k in ('from', 'to', 'amount')) and isinstance(transaction['amount'], int) and transaction['amount'] > 0: valid_tx = True
             else: valid_tx = True
        if not valid_tx: print("[Error] Invalid local tx format."); return
        should_add = True
        if transaction['type'] == TX_TRANSFER_ECASH and transaction['from'] != SYSTEM_ACCOUNT:
             sender_balance = self.get_current_balance(transaction['from'])
             if sender_balance < transaction['amount']: print("[Error] Insufficient balance for local tx from {}. ".format(transaction['from'])); should_add = False # Use format
        if should_add:
             if 'timestamp' not in transaction: transaction['timestamp'] = str(datetime.now())
             with self.lock:
                  tx_repr = json.dumps(transaction, sort_keys=True)
                  if not any(json.dumps(tx, sort_keys=True) == tx_repr for tx in self.pending_transactions):
                       self.pending_transactions.append(transaction); print("\n[Node] Added local transaction: {}".format(transaction['type'])); self.broadcast(MSG_TYPE_NEW_TRANSACTION, transaction) # Use format

    def mine_block_local(self):
        new_block = None; block_added = False; generated_tx = []
        with self.lock:
            if not self.pending_transactions: print("\n[Node] No pending tx."); return False
            print("\n[Node] Mining block #{}...".format(len(self.blockchain.chain))); latest_block = self.blockchain.get_latest_block(); # Use format
            if not latest_block: print("[Error] No Genesis."); return False
            valid_tx_for_block = []; temp_balances = self.get_balances_up_to_block(latest_block.hash); candidate_txs = list(self.pending_transactions)
            for tx in candidate_txs:
                 valid_for_block = True
                 if tx.get('type') == TX_TRANSFER_ECASH:
                      sender, amount = tx.get('from'), tx.get('amount', 0)
                      if sender != SYSTEM_ACCOUNT and temp_balances.get(sender, 0) < amount: print("[Miner] Skipping pending tx: Insufficient funds {}".format(tx['from'])); valid_for_block = False # Use format
                      else: temp_balances[sender] = temp_balances.get(sender, 0) - amount; recipient = tx.get('to'); temp_balances[recipient] = temp_balances.get(recipient, 0) + amount
                 if valid_for_block: valid_tx_for_block.append(tx)
            if not valid_tx_for_block: print("[Miner] No valid tx for block."); return False
            new_block = Block( index=latest_block.index + 1, timestamp=datetime.now(), transactions=valid_tx_for_block, previous_hash=latest_block.hash ); new_block.hash = new_block.calculate_hash()
            if self.blockchain.add_block(new_block):
                 print("[Node] Mined/Added Block {}.".format(new_block.index)); block_added = True; self._update_balances_from_block(new_block) # Use format
                 mined_tx_ids = set(json.dumps(tx, sort_keys=True) for tx in valid_tx_for_block)
                 self.pending_transactions = [ tx for tx in self.pending_transactions if json.dumps(tx, sort_keys=True) not in mined_tx_ids ]
                 print("[Node] Balances updated. Pending tx: {}".format(len(self.pending_transactions))) # Use format
                 generated_tx = self._generate_system_transfers_for_block(new_block)
        if block_added and new_block:
            self.broadcast(MSG_TYPE_NEW_BLOCK, new_block);
            for sys_tx in generated_tx: self.add_transaction_local(sys_tx)
            return True
        return False

    def resolve_conflicts(self, received_chain):
        replaced = False
        with self.lock:
            current_len = len(self.blockchain.chain); received_len = len(received_chain)
            if received_len > current_len:
                temp_blockchain = Blockchain(); temp_blockchain.chain = received_chain
                if temp_blockchain.is_chain_valid() and self._validate_chain_balances(received_chain):
                    print("[Sync] Received chain valid (len {}). Replacing.".format(received_len)); self.blockchain.chain = received_chain # Use format
                    self._reconcile_pending_transactions(); self._recalculate_all_balances(); replaced = True
        return replaced

    def request_chain_from_peers(self):
        print("[Sync] Requesting blockchain from peers..."); self.broadcast(MSG_TYPE_REQUEST_CHAIN, "")
    def _initial_sync(self):
        time.sleep(10); self.request_chain_from_peers()
    def _reconcile_pending_transactions(self):
        all_tx_in_chain = set();
        for block in self.blockchain.chain:
             for tx in block.transactions: all_tx_in_chain.add(json.dumps(tx, sort_keys=True))
        self.pending_transactions = [ tx for tx in self.pending_transactions if json.dumps(tx, sort_keys=True) not in all_tx_in_chain ]

    # --- Balance and Ledger Logic ---
    def _update_balances_from_block(self, block):
        with self.lock:
             for tx in block.transactions:
                  if tx.get('type') == TX_TRANSFER_ECASH:
                       sender, recipient, amount = tx.get('from'), tx.get('to'), tx.get('amount', 0)
                       if sender not in E_CASH_BALANCES: E_CASH_BALANCES[sender] = 0
                       if recipient not in E_CASH_BALANCES: E_CASH_BALANCES[recipient] = 0
                       E_CASH_BALANCES[sender] -= amount; E_CASH_BALANCES[recipient] += amount
    def _recalculate_all_balances(self):
        print("[Balance] Recalculating all balances...");
        with self.lock:
             temp_balances = {user: 0 for user in USERS}; temp_balances[SYSTEM_ACCOUNT] = INITIAL_SYSTEM_BALANCE
             chain_copy = list(self.blockchain.chain)
             for block in chain_copy:
                  for tx in block.transactions:
                       if tx.get('type') == TX_TRANSFER_ECASH:
                            sender, recipient, amount = tx.get('from'), tx.get('to'), tx.get('amount',0)
                            if sender not in temp_balances: temp_balances[sender] = 0
                            if recipient not in temp_balances: temp_balances[recipient] = 0
                            temp_balances[sender] -= amount; temp_balances[recipient] += amount
             global E_CASH_BALANCES; E_CASH_BALANCES = temp_balances
        print("[Balance] Recalculation complete.")
    def get_current_balance(self, username):
        temp_balances = self._get_balances_from_chain(); return temp_balances.get(username, 0)
    def get_balances_up_to_block(self, block_hash):
         balances = {user: 0 for user in USERS}; balances[SYSTEM_ACCOUNT] = INITIAL_SYSTEM_BALANCE
         with self.lock:
              chain_copy = list(self.blockchain.chain)
              for block in chain_copy:
                   for tx in block.transactions:
                        if tx.get('type') == TX_TRANSFER_ECASH:
                             sender, recipient, amount = tx.get('from'), tx.get('to'), tx.get('amount',0)
                             if sender not in balances: balances[sender] = 0;
                             if recipient not in balances: balances[recipient] = 0
                             balances[sender] -= amount; balances[recipient] += amount
                   if block.hash == block_hash: break
         return balances
    def _get_balances_from_chain(self):
        balances = {user: 0 for user in USERS}; balances[SYSTEM_ACCOUNT] = INITIAL_SYSTEM_BALANCE
        with self.lock:
             chain_copy = list(self.blockchain.chain)
             for block in chain_copy:
                  for tx in block.transactions:
                       if tx.get('type') == TX_TRANSFER_ECASH:
                            sender, recipient, amount = tx.get('from'), tx.get('to'), tx.get('amount',0)
                            if sender not in balances: balances[sender] = 0;
                            if recipient not in balances: balances[recipient] = 0
                            balances[sender] -= amount; balances[recipient] += amount
        return balances
    def _validate_chain_balances(self, chain):
        temp_balances = {user: 0 for user in USERS}; temp_balances[SYSTEM_ACCOUNT] = INITIAL_SYSTEM_BALANCE
        for block in chain:
             current_block_balances = temp_balances.copy()
             for tx in block.transactions:
                  if tx.get('type') == TX_TRANSFER_ECASH:
                       sender, amount = tx.get('from'), tx.get('amount', 0)
                       if sender != SYSTEM_ACCOUNT and current_block_balances.get(sender, 0) < amount: print("[Chain Validation] Invalid transfer in block {}: {}".format(block.index, tx)); return False # Use format
                       current_block_balances[sender] = current_block_balances.get(sender, 0) - amount
                       recipient = tx.get('to'); current_block_balances[recipient] = current_block_balances.get(recipient, 0) + amount
             temp_balances = current_block_balances
        return True
    def _generate_system_transfers_for_block(self, block):
        generated_tx = [];
        with self.lock: chain_history_copy = list(self.blockchain.chain)
        def get_history_from_copy(patient_id, chain_copy):
             history = [];
             for b in chain_copy:
                  if b.index > block.index: continue
                  for t in b.transactions:
                       if isinstance(t, dict) and t.get('patient_id') == patient_id: history.append({'transaction': t})
             return history
        for tx in block.transactions:
             if not isinstance(tx, dict): continue; patient_id = tx.get('patient_id');
             if not patient_id: continue
             if tx.get('type') == 'LAB_TEST_RESULT':
                  history = get_history_from_copy(patient_id, chain_history_copy); ordering_doctor = None
                  for record in reversed(history):
                       prev_tx = record['transaction']
                       if (prev_tx.get('type') == 'DOCTOR_CONSULTATION' and tx.get('test_name') in prev_tx.get('tests_ordered', []) and prev_tx.get('patient_id') == patient_id): ordering_doctor = prev_tx.get('doctor'); break
                  if ordering_doctor:
                       reward_tx = {"type": TX_TRANSFER_ECASH, "from": SYSTEM_ACCOUNT, "to": ordering_doctor, "amount": 500, "reason": "Reward for Lab Test Order ({})".format(tx.get('test_name')), "timestamp": str(datetime.now())} # Use format
                       generated_tx.append(reward_tx); print("[Reward Gen] System -> {} (500 units) for test in block {}".format(ordering_doctor, block.index)) # Use format
             elif tx.get('type') == 'PRESCRIPTION_FILLED':
                  ref_ts = tx.get('references_prescription_timestamp'); prescribing_doctor = None; history = get_history_from_copy(patient_id, chain_history_copy)
                  for record in reversed(history):
                       prev_tx = record['transaction']
                       if (prev_tx.get('type') == 'PRESCRIPTION' and prev_tx.get('timestamp') == ref_ts and prev_tx.get('patient_id') == patient_id): prescribing_doctor = prev_tx.get('prescribed_by'); break
                  if prescribing_doctor:
                       reward_tx = {"type": TX_TRANSFER_ECASH, "from": SYSTEM_ACCOUNT, "to": prescribing_doctor, "amount": 700, "reason": "Reward for Prescription Fill", "timestamp": str(datetime.now())}
                       generated_tx.append(reward_tx); print("[Reward Gen] System -> {} (700 units) for fill in block {}".format(prescribing_doctor, block.index)) # Use format
        return generated_tx

    # --- User Interface Methods ---
    def login(self, username, password):
        if self.current_user: print("Already logged in as {}".format(self.current_user['name'])); return self.current_user # Use format
        user_info = USERS.get(username)
        if user_info and user_info["password"] == password: print("Login successful! Welcome {} ({})".format(user_info['name'], user_info['role'])); self.current_user = {"username": username, **user_info}; return self.current_user # Use format
        else: print("Invalid username or password."); self.current_user = None; return None
    def logout(self):
        if self.current_user: print("Logging out {}.".format(self.current_user['name'])); self.current_user = None # Use format
        else: print("Not logged in.")

    def view_balances(self):
        """ Displays ledger balances from the local cache. """
        print("\n--- Ledger Balances (e-cash units) ---")
        with self.lock:
             sorted_users = sorted(E_CASH_BALANCES.keys())
             # --- FIXED LINE ---
             for user in sorted_users:
                 # Use .format() instead of f-string
                 print("{}: {}".format(user, E_CASH_BALANCES.get(user, 0)))
             # --- END FIX ---
        print("------------------------------------")

    def view_patient_history(self, patient_id):
        print("\n--- Patient History for ID: {} (Node {}) ---".format(patient_id, self.node_id)) # Use format
        with self.lock: history = self.blockchain.get_patient_history(patient_id)
        if not history: print("No records found..."); return
        for record in history:
             print("\nBlock #{} ({})".format(record['block_index'], record['timestamp'])) # Use format
             try: print(json.dumps(record['transaction'], indent=2))
             except TypeError: print(str(record['transaction']))
        print("-" * 30)

    # --- Workflow Actions ---
    def register_new_patient(self, patient_name):
        if not self.current_user or self.current_user['role'] != 'doctor': return None, "Permission denied."
        patient_id = str(uuid.uuid4()); timestamp = str(datetime.now()); registered_by = self.current_user['username']
        transaction = { "type": "PATIENT_REGISTRATION", "patient_id": patient_id, "patient_name": patient_name, "registered_by": registered_by, "timestamp": timestamp }
        # Write to CSV
        write_header = not os.path.exists(PATIENT_CSV_FILENAME)
        try:
            with self.csv_lock:
                 with open(PATIENT_CSV_FILENAME, 'a', newline='') as csvfile:
                      writer = csv.writer(csvfile)
                      if write_header: writer.writerow(PATIENT_CSV_HEADER)
                      writer.writerow([patient_id, patient_name, registered_by, timestamp])
                 print("[CSV] Patient {} details logged to {}".format(patient_name, PATIENT_CSV_FILENAME)) # Use format
        except IOError as e: print("[Error] Could not write to CSV file {}: {}".format(PATIENT_CSV_FILENAME, e)) # Use format
        self.add_transaction_local(transaction)
        return patient_id, "Registration tx created for {} (ID: {}) and logged to CSV.".format(patient_name, patient_id) # Use format

    def doctor_consultation(self, patient_id, notes, order_test_flag):
        if not self.current_user or self.current_user['role'] != 'doctor': return "Permission denied."
        if not patient_id: return "No active patient selected."
        transaction = { "type": "DOCTOR_CONSULTATION", "patient_id": patient_id, "doctor": self.current_user['username'], "notes": notes, "tests_ordered": ["Blood Test"] if order_test_flag else [], "timestamp": str(datetime.now()) }
        self.add_transaction_local(transaction); return "Consultation transaction created."
    def perform_blood_test(self, patient_id, results_dict):
        if not self.current_user or self.current_user['role'] != 'lab': return "Permission denied."
        if not patient_id: return "No active patient selected."
        transaction = { "type": "LAB_TEST_RESULT", "patient_id": patient_id, "test_name": "Blood Test", "performed_by": self.current_user['username'], "results": results_dict, "timestamp": str(datetime.now()) }
        self.add_transaction_local(transaction); return "Blood test result transaction created."
    def doctor_review_results_and_prescribe(self, patient_id, prescription_details, reviewed_lab_user):
        if not self.current_user or self.current_user['role'] != 'doctor': return "Permission denied."
        if not patient_id: return "No active patient selected."
        doctor_user = self.current_user['username']; payment_amount = 100; doctor_balance = self.get_current_balance(doctor_user); transfer_possible = False
        if doctor_balance >= payment_amount: transfer_possible = True
        else: print("[Warning] Doctor {} has insufficient funds ({}) to pay lab ({}).".format(doctor_user, doctor_balance, payment_amount)) # Use format
        presc_tx = { "type": "PRESCRIPTION", "patient_id": patient_id, "prescribed_by": doctor_user, **prescription_details, "based_on_review_of_test_by": reviewed_lab_user, "timestamp": str(datetime.now()) }
        self.add_transaction_local(presc_tx); final_msg = "Prescription transaction created. "
        if transfer_possible and reviewed_lab_user:
            transfer_tx = { "type": TX_TRANSFER_ECASH, "from": doctor_user, "to": reviewed_lab_user, "amount": payment_amount, "reason": "Payment for Lab Report Access", "timestamp": str(datetime.now()) }
            self.add_transaction_local(transfer_tx); final_msg += "Payment transaction ({} units to {}) created.".format(payment_amount, reviewed_lab_user) # Use format
        elif not reviewed_lab_user: final_msg += "(Could not identify lab user for payment)."
        else: final_msg += "(Payment skipped due to insufficient funds)."
        return final_msg
    def pharmacy_fill_prescription(self, patient_id, prescription_timestamp):
        if not self.current_user or self.current_user['role'] != 'pharmacy': return "Permission denied."
        if not patient_id: return "No active patient selected."
        transaction = { "type": "PRESCRIPTION_FILLED", "patient_id": patient_id, "filled_by_pharmacy": self.current_user['username'], "references_prescription_timestamp": prescription_timestamp, "timestamp": str(datetime.now()) }
        self.add_transaction_local(transaction); return "Prescription filled transaction created."

# --- Helper Function for Argument Parsing ---
def parse_arguments():
    parser = argparse.ArgumentParser(description="Run a Healthcare Blockchain Node")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP")
    parser.add_argument("--port", type=int, required=True, help="Port")
    parser.add_argument("--peers", type=str, default="", help="Comma-separated peers (host:port)")
    parser.add_argument("--id", type=str, help="Optional node ID")
    args = parser.parse_args()
    peer_list = []
    if args.peers:
        for peer_str in args.peers.split(','):
            try: host, port_str = peer_str.strip().split(':'); peer_list.append((host, int(port_str)))
            except ValueError: pass
    return args.host, args.port, peer_list, args.id