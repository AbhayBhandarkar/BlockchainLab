# doctor_node.py

import sys
import json
import traceback
from node_common import Node, parse_arguments # Import Node class and parser

def run_doctor_interface(node):
    """ Runs the interactive command loop for the Doctor Node. """
    active_patient_id = None
    print("\n--- Doctor Node Interface ---")
    print("Type 'help' for commands.")

    while True:
        prompt = "Doc@{} ({}): ".format(node.node_id, active_patient_id or 'No Patient') # Use format
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
                print("  login                   Login as doctor")
                print("  logout                  Logout")
                print("  register                Register new patient")
                print("  consult                 Consultation/Order tests (needs active patient)")
                print("  prescribe               Review results & Prescribe (needs active patient)")
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
                    if user_info and user_info['role'] != 'doctor':
                         print("Error: This user is not a doctor.")
                         node.logout()
                else: print("Already logged in.")

            elif command == "logout":
                node.logout()
                active_patient_id = None

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

            # --- Doctor Specific Commands ---
            elif node.current_user and node.current_user['role'] == 'doctor':
                if command == "register":
                    patient_name = input("Enter patient's full name: ")
                    if patient_name:
                         new_id, msg = node.register_new_patient(patient_name)
                         print(msg)
                         if new_id: active_patient_id = new_id
                    else: print("Registration cancelled.")

                elif command == "set_patient" and len(command_parts) > 1:
                    active_patient_id = command_parts[1]
                    print("Active patient set to: {}".format(active_patient_id)) # Use format

                elif command == "history":
                    if active_patient_id: node.view_patient_history(active_patient_id)
                    else: print("No active patient set.")

                elif command == "consult":
                    if active_patient_id:
                        notes = input("Enter consultation notes: ")
                        order_test = input("Order blood test? (y/n): ").lower() == 'y'
                        msg = node.doctor_consultation(active_patient_id, notes, order_test)
                        print(msg)
                    else: print("No active patient set.")

                elif command == "prescribe":
                    if active_patient_id:
                         print("\nReviewing patient history before prescribing:")
                         node.view_patient_history(active_patient_id)

                         reviewed_lab_user = None
                         with node.lock: history = node.blockchain.get_patient_history(active_patient_id)
                         for record in reversed(history):
                              tx = record['transaction']
                              if tx.get('type') == 'LAB_TEST_RESULT' and tx.get('test_name') == 'Blood Test':
                                   reviewed_lab_user = tx.get('performed_by')
                                   print("(Found relevant test result by: {})".format(reviewed_lab_user)) # Use format
                                   break
                         if not reviewed_lab_user:
                              print("(Warning: Could not find specific lab result to link payment to.)")

                         print("\nEnter prescription details:")
                         details = { "medication": input("Medication: "), "dosage": input("Dosage: "),
                                     "frequency": input("Frequency: "), "duration": input("Duration: ") }
                         if all(details.values()):
                              msg = node.doctor_review_results_and_prescribe(active_patient_id, details, reviewed_lab_user)
                              print(msg)
                         else: print("Prescription cancelled (missing details).")
                    else: print("No active patient set.")
                else: print("Unknown command or requires login.")
            elif command in ["register", "consult", "prescribe", "set_patient", "history"]:
                 print("Command requires doctor login.")
            else: print("Unknown command.")

        except EOFError: break
        except Exception as e: print("\nAn error occurred: {}".format(e)); traceback.print_exc() # Use format

def main():
    host, port, peer_list, node_id = parse_arguments()
    if not node_id: node_id = "DoctorNode-{}".format(port) # Use format

    node = Node(host, port, peer_list, node_id)
    node.start()

    try: run_doctor_interface(node)
    except KeyboardInterrupt: print("\nCtrl+C detected...")
    finally: node.stop(); print("Doctor Node shutdown complete.")

if __name__ == "__main__":
    main()