# lab_node.py

import sys
import json
import traceback
from node_common import Node, parse_arguments

def run_lab_interface(node):
    active_patient_id = None
    print("\n--- Lab Node Interface ---")
    print("Type 'help' for commands.")
    while True:
        prompt = "Lab@{} ({}): ".format(node.node_id, active_patient_id or 'No Patient') # Use format
        if node.current_user:
            prompt = "{}@{} ({}): ".format(node.current_user['username'], node.node_id, active_patient_id or 'No Patient') # Use format
        try:
            user_input = input(prompt).strip()
            if not user_input: continue
            command_parts = user_input.split()
            command = command_parts[0].lower()

            if command == "exit": break
            elif command == "help":
                print("\nAvailable Commands:")
                print("  login                   Login as lab tech")
                print("  logout                  Logout")
                print("  perform_test            Perform blood test (needs active patient)")
                print("  set_patient <id>        Set active patient")
                print("  history                 View history for active patient")
                print("  mine                    Mine pending transactions")
                print("  chain                   View local blockchain")
                print("  pending                 View pending transactions")
                print("  peers                   View connected peers")
                print("  balances                View e-cash balances (Ledger View)")
                print("  sync                    Request chain sync from peers")
                print("  recalc_balances         Recalculate balances from chain")
                print("  exit                    Stop the node")

            elif command == "login":
                if not node.current_user:
                    username = input("Enter username: ")
                    password = input("Enter password: ")
                    user_info = node.login(username, password)
                    if user_info and user_info['role'] != 'lab': print("Error: User not a lab tech."); node.logout()
                else: print("Already logged in.")
            elif command == "logout": node.logout(); active_patient_id = None
            elif command == "mine": node.mine_block_local()
            elif command == "chain":
                 with node.lock: print(node.blockchain)
            elif command == "pending":
                 with node.lock: print("Pending Transactions: {}".format(json.dumps(node.pending_transactions, indent=2))) # Use format
            elif command == "peers":
                 with node.lock: print("Connected Peers: {}".format(list(node.peers.keys()))) # Use format
            elif command == "balances": node.view_balances()
            elif command == "sync": node.request_chain_from_peers()
            elif command == "recalc_balances": node._recalculate_all_balances()

            # --- Lab Specific Commands ---
            elif node.current_user and node.current_user['role'] == 'lab':
                if command == "set_patient" and len(command_parts) > 1:
                    active_patient_id = command_parts[1]
                    print("Active patient set to: {}".format(active_patient_id)) # Use format
                elif command == "history":
                    if active_patient_id: node.view_patient_history(active_patient_id)
                    else: print("No active patient set.")
                elif command == "perform_test":
                    if active_patient_id:
                         print("Enter blood test results:")
                         results = { "Hemoglobin": input("Hemoglobin: "), "WBC Count": input("WBC Count: "), "Platelets": input("Platelets: ") }
                         if all(results.values()):
                              msg = node.perform_blood_test(active_patient_id, results)
                              print(msg)
                         else: print("Test data entry cancelled.")
                    else: print("No active patient set.")
                else: print("Unknown command or requires login.")
            elif command in ["perform_test", "set_patient", "history"]:
                 print("Command requires lab technician login.")
            else: print("Unknown command.")

        except EOFError: break
        except Exception as e: print("\nAn error occurred: {}".format(e)); traceback.print_exc() # Use format

def main():
    host, port, peer_list, node_id = parse_arguments()
    if not node_id: node_id = "LabNode-{}".format(port) # Use format
    node = Node(host, port, peer_list, node_id)
    node.start()
    try: run_lab_interface(node)
    except KeyboardInterrupt: print("\nCtrl+C detected...")
    finally: node.stop(); print("Lab Node shutdown complete.")

if __name__ == "__main__":
    main()