# Healthcare Blockchain Simulation

**(Project State as of: March 26, 2025)**

A Python-based simulation demonstrating the application of blockchain concepts to manage healthcare interactions between a Doctor, Diagnostic Lab, and Pharmacy. It features multiple nodes communicating over sockets, transaction processing, block mining simulation, an e-cash incentive system with explicit transfers, and basic CSV logging for patient registration.

## Goal

To provide an educational tool illustrating how a simplified blockchain network can maintain a distributed ledger of patient-related events (registration, tests, prescriptions) and facilitate value exchange (e-cash incentives/payments) between participating entities.

## Features

* **Multi-Node Simulation:** Runs Doctor, Lab, and Pharmacy nodes as separate processes.
* **Peer-to-Peer Networking:** Uses Python's `socket` library for basic node communication (broadcasting transactions and blocks).
* **Blockchain Core:** Implements basic `Block` and `Blockchain` structures with SHA-256 hashing.
* **Transaction Types:** Handles various healthcare events:
    * `PATIENT_REGISTRATION`
    * `DOCTOR_CONSULTATION`
    * `LAB_TEST_RESULT`
    * `PRESCRIPTION`
    * `PRESCRIPTION_FILLED`
    * `TRANSFER_ECASH` (for payments/rewards)
* **Simulated Mining:** A `mine` command bundles pending transactions into a new block.
* **E-Cash Ledger:** An explicit ledger system based on `TRANSFER_ECASH` transactions. Balances are derived from the blockchain history.
    * Doctor pays Lab for accessing test results (when prescribing).
    * A `SYSTEM_ACCOUNT` rewards Doctors for test orders and filled prescriptions.
* **Balance Validation:** Checks sender balance before validating/including `TRANSFER_ECASH` transactions.
* **Conflict Resolution:** Basic "longest valid chain wins" rule for synchronization.
* **CSV Logging:** Patient registration details are appended to `patient_registry.csv`.
* **Interactive CLI:** Each node type has a command-line interface for user interaction.

## Technology Stack

* **Python 3** (Code uses `.format()` for compatibility, likely works on 3.5+)
* Standard Python Libraries:
    * `socket`
    * `threading`
    * `pickle` (Note: Security implications - used for simplicity in simulation)
    * `json`
    * `hashlib`
    * `datetime`
    * `uuid`
    * `csv`
    * `os`
    * `argparse`
    * `traceback`

## Core Concepts Demonstrated

* **Blocks & Chaining:** Data is grouped into blocks linked cryptographically.
* **Hashing:** Ensures data integrity and block linkage.
* **Decentralization (Simulated):** Multiple nodes maintain their own copy of the blockchain and synchronize.
* **Transactions:** Atomic units representing events or value transfers.
* **Distributed Ledger:** The blockchain serves as the shared, immutable record of all transactions and the basis for deriving account balances.
* **P2P Networking:** Nodes directly communicate to share information.
* **Incentive Mechanisms:** Rewarding participation through e-cash transfers recorded on-chain.

## System Architecture

The project consists of the following Python files:

1.  **`blockchain_core.py`:** Defines the fundamental `Block` and `Blockchain` data structures.
2.  **`node_common.py`:** Contains the main `Node` class, encapsulating all common logic:
    * Networking (server setup, peer connections, message handling via sockets).
    * Blockchain management (synchronization, validation, conflict resolution).
    * Transaction handling (adding, broadcasting, basic validation).
    * Mining simulation (`mine_block_local`).
    * Balance/Ledger management (calculating/updating balances based on transfers).
    * Workflow action methods (called by role-specific nodes).
    * Shared constants, user dictionary (`USERS`), and balance dictionary (`E_CASH_BALANCES`).
    * CSV writing for patient registration.
3.  **`doctor_node.py`:** An executable script that:
    * Imports the `Node` class from `node_common`.
    * Parses command-line arguments (port, peers).
    * Instantiates and starts a `Node`.
    * Provides an interactive command-line interface tailored for **Doctor** actions (register, consult, prescribe, etc.).
4.  **`lab_node.py`:** Similar to `doctor_node.py`, but provides the interface for **Lab Technician** actions (perform\_test).
5.  **`pharmacy_node.py`:** Similar to `doctor_node.py`, but provides the interface for **Pharmacist** actions (fill).
6.  **`patient_registry.csv`:** A CSV file (created automatically when the first patient is registered) logging basic details (`patient_id`, `name`, `registered_by`, `timestamp`).

**(Note: The full source code for the `.py` files is not included in this README but should reside in the repository alongside it.)**

## Setup and Installation

1.  **Prerequisites:** Ensure you have Python 3 installed on your system.
2.  **Get Code:** Download or clone the repository, or save the 5 Python files (`blockchain_core.py`, `node_common.py`, `doctor_node.py`, `lab_node.py`, `pharmacy_node.py`) into a single directory on your computer.

## How to Run

1.  **Open Terminals:** You need three separate terminal windows or command prompts.
2.  **Navigate:** In **each** terminal, use the `cd` command to navigate into the directory where you saved the Python files.
    ```bash
    cd path/to/your/project_directory
    ```
3.  **Start Nodes:** Execute the following commands, one in each terminal:

    * **Terminal 1 (Doctor Node):**
        ```bash
        python3 doctor_node.py --port 5001 --peers 127.0.0.1:5002,127.0.0.1:5003
        ```
        * `--port 5001`: This node listens on port 5001.
        * `--peers ...`: It will try to connect to nodes on ports 5002 and 5003.

    * **Terminal 2 (Lab Node):**
        ```bash
        python3 lab_node.py --port 5002 --peers 127.0.0.1:5001,127.0.0.1:5003
        ```
        * `--port 5002`: This node listens on port 5002.
        * `--peers ...`: It will try to connect to nodes on ports 5001 and 5003.

    * **Terminal 3 (Pharmacy Node):**
        ```bash
        python3 pharmacy_node.py --port 5003 --peers 127.0.0.1:5001,127.0.0.1:5002
        ```
        * `--port 5003`: This node listens on port 5003.
        * `--peers ...`: It will try to connect to nodes on ports 5001 and 5002.

4.  **Verify:** Each terminal should show initialization messages, indicate the server is listening, and potentially show successful peer connection messages. You will see a command prompt like `Doc@DoctorNode-5001 (No Patient) >` waiting for input.

## Available Logins

Use these credentials with the `login` command:

* **Doctor:**
    * Username: `dr_alice`
    * Password: `password123`
* **Lab Technician:**
    * Username: `lab_tech_bob`
    * Password: `labpass`
* **Pharmacy:**
    * Username: `pharm_charlie`
    * Password: `pharmpass`

## Example Simulation Workflow

1.  **Doctor Node (Terminal 1):**
    * `login` (as `dr_alice`)
    * `register` (enter name, e.g., "Jane Doe") -> **Note the Patient ID displayed!**
    * `consult` (enter notes, order test: `y`)
2.  **Any Node (e.g., Terminal 2):**
    * `mine` (Block #1 containing registration & consult is mined and broadcast)
3.  **Lab Node (Terminal 2):**
    * `login` (as `lab_tech_bob`)
    * `set_patient <PASTE_PATIENT_ID>`
    * `perform_test` (enter results)
4.  **Any Node (e.g., Terminal 3):**
    * `mine` (Block #2 containing lab results is mined) -> This triggers reward generation.
    * `pending` (Optional: See the `SYSTEM -> dr_alice` transfer tx)
5.  **Any Node (e.g., Terminal 1):**
    * `mine` (Block #3 containing the first system reward is mined)
    * `balances` (Check: `dr_alice` should have 500 e-cash)
6.  **Doctor Node (Terminal 1):**
    * `prescribe` (Enter medication details) -> Creates `PRESCRIPTION` and `TRANSFER_ECASH` (Dr -> Lab, if funds exist) txs.
7.  **Any Node (e.g., Terminal 2):**
    * `mine` (Block #4 containing prescription and payment is mined)
    * `balances` (Check: `dr_alice` balance reduced by 100, `lab_tech_bob` increased by 100)
8.  **Pharmacy Node (Terminal 3):**
    * `login` (as `pharm_charlie`)
    * `set_patient <PASTE_PATIENT_ID>`
    * `fill` (Confirm: `y`)
9.  **Any Node (e.g., Terminal 1):**
    * `mine` (Block #5 containing fill confirmation is mined) -> Triggers reward generation.
    * `pending` (Optional: See the second `SYSTEM -> dr_alice` transfer tx)
10. **Any Node (e.g., Terminal 2):**
    * `mine` (Block #6 containing the second system reward is mined)
    * `balances` (Check: `dr_alice` balance increased by 700)
11. **Explore:** Use commands like `history`, `chain`, `peers`, `sync`. Check `patient_registry.csv`.
12. **Stop:** Type `exit` or press `Ctrl+C` in each terminal when finished.

## Key Commands Summary

* `help`: Show available commands for the current node interface.
* `login`: Log in using predefined credentials.
* `logout`: Log out the current user.
* `register`: (Doctor) Register a new patient.
* `consult`: (Doctor) Create a consultation record, optionally order tests.
* `perform_test`: (Lab) Record results for a blood test.
* `prescribe`: (Doctor) Review history and create a prescription (also triggers payment to Lab).
* `fill`: (Pharmacy) Mark a prescription as filled.
* `set_patient <ID>`: Set the active patient context for commands like `history`, `perform_test`, `prescribe`, `fill`.
* `history`: View the transaction history for the active patient from the node's blockchain copy.
* `mine`: Attempt to mine a new block containing valid pending transactions.
* `chain`: Display the node's current copy of the entire blockchain.
* `pending`: Show transactions waiting to be mined.
* `balances`: Display the current e-cash balances (ledger view) derived from the blockchain.
* `peers`: List the addresses of currently connected peer nodes.
* `sync`: Request the full blockchain from peers to resolve potential inconsistencies.
* `recalc_balances`: Force recalculation of balances from the entire blockchain history (useful after `sync`).
* `exit`: Stop the node process.

## Limitations & Future Improvements

* **Consensus:** Uses a highly simplified "mining" process. No real consensus algorithm (like PoW or PoS) is implemented. Any node can mine.
* **Security:**
    * Uses `pickle` for network serialization, which is insecure. JSON with validation would be better.
    * Passwords are plain text. Hashing is required for real use.
    * No transaction signing or cryptographic identity verification.
* **Validation:** Transaction validation is basic (format checks, balance checks for transfers). More robust validation rules could be added.
* **Networking:** Error handling and peer management are basic. Does not handle complex network partitions or sophisticated peer discovery.
* **Scalability:** Mining one block per action and querying full history can be inefficient for large chains.
* **No Patient Interface:** Patients cannot directly interact with the system in this simulation.
* **CSV Concurrency:** While a lock is used, heavy simultaneous writes to the CSV file (unlikely in simulation) could theoretically still pose issues depending on the OS and filesystem.

Future improvements could include implementing a proper consensus mechanism, adding digital signatures, using a safer serialization format, enhancing network robustness, implementing more granular access control, and potentially adding a patient-facing interface.