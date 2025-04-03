# CBC (Cipher Block Chaining mode), CTR (Counter mode), and OpenSSL Crypto

## Introduction

This project provides functional examples demonstrating common symmetric encryption techniques using Python and OpenSSL command-line tools. It covers:

1.  **AES Encryption in Python:** Using the `cryptography` library to implement:
    * Cipher Block Chaining (CBC) mode.
    * Counter (CTR) mode.
    * Focuses on secure practices like using cryptographically secure random Initialization Vectors (IVs) and Nonces for each encryption.
2.  **File Encryption with OpenSSL:**
    * Using `openssl enc` for password-based symmetric encryption of files.
    * Using `openssl cms` for encryption based on recipient certificates (enveloping).

These examples illustrate how to encrypt and decrypt data, such as simulated transaction payloads, but **do not** implement a full blockchain system.

## File Overview

This project consists of the following key files:

* **`requirements.txt`**: Lists the necessary Python package (`cryptography`).
* **`secure_crypto.py`**: Contains the Python implementations of AES-CBC and AES-CTR encryption and decryption functions.
* **`openssl_commands.sh`**: A shell script demonstrating file encryption/decryption using `openssl enc` with a password.
* **`openssl_cms_commands.sh`**: A shell script demonstrating file encryption/decryption using `openssl cms` with public key certificates.

## Prerequisites

Before running the examples, ensure you have the following installed:

* **Python 3:** Version 3.6 or higher recommended.
    * Check: `python3 --version`
* **pip:** Python's package installer.
    * Check: `pip --version` or `python3 -m pip --version`
* **OpenSSL:** The command-line cryptography toolkit.
    * Check: `openssl version`
    * Installation varies by OS (e.g., `sudo apt install openssl`, `brew install openssl`). Often pre-installed on Linux/macOS.

## Setup & Running Instructions

1.  **Save Files:** Create a directory for this project (e.g., `crypto_examples`) and save the four files (`requirements.txt`, `secure_crypto.py`, `openssl_commands.sh`, `openssl_cms_commands.sh`) inside it.
2.  **Navigate:** Open your terminal or command prompt and navigate into the project directory: `cd crypto_examples`
3.  **Set Up Python Environment (Recommended):**
    ```bash
    # Create virtual environment
    python3 -m venv venv
    # Activate (Linux/macOS)
    source venv/bin/activate
    # Activate (Windows cmd/powershell - use 'venv\Scripts\activate')
    ```
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Run Python Script:**
    ```bash
    python3 secure_crypto.py
    ```
    * *Expected Output:* Logs showing key generation, CBC/CTR encryption/decryption steps, unique IVs/Nonces per message, and verification results.
6.  **Make Shell Scripts Executable (Linux/macOS):**
    ```bash
    chmod +x openssl_commands.sh
    chmod +x openssl_cms_commands.sh
    ```
7.  **Run OpenSSL `enc` Script:**
    ```bash
    ./openssl_commands.sh
    ```
    * *Expected Output:* Creation of plaintext/ciphertext files, optional Base64 steps, decryption logs, verification result, and cleanup reminder.
8.  **Run OpenSSL `cms` Script:**
    ```bash
    ./openssl_cms_commands.sh
    ```
    * *Expected Output:* Generation of a key/certificate pair (if needed), creation of plaintext/enveloped files, decryption logs, verification result, and cleanup reminder.
9.  **Deactivate Virtual Environment (When finished):**
    ```bash
    deactivate
    ```

## Detailed File Explanations

---

### `secure_crypto.py`

* **Purpose:** Provides Python functions for encrypting and decrypting data using AES in CBC and CTR modes, emphasizing security best practices.
* **Key Concepts:** Symmetric Encryption, AES (Advanced Encryption Standard), Modes of Operation (CBC, CTR), Padding (PKCS7), Initialization Vectors (IVs), Nonces, Cryptographically Secure Random Number Generation (`os.urandom`).

#### CBC Mode Explanation

Cipher Block Chaining links blocks together by XORing the *previous* ciphertext block with the *current* plaintext block before encryption. This ensures identical plaintext blocks encrypt differently.

* **Padding:** Since CBC works on fixed-size blocks (16 bytes for AES), plaintext must be padded (e.g., using PKCS7) to a multiple of the block size before encryption.
* **IV:** A unique, random Initialization Vector (IV) is XORed with the *first* plaintext block. It must be unpredictable for security and unique for a given key to prevent leaks.

* **Encryption Process:**
    1.  Generate a unique, random IV (16 bytes).
    2.  Pad the plaintext `P` to get `P_padded`.
    3.  Split `P_padded` into blocks `P_1, P_2, ..., P_n`.
    4.  Calculate ciphertext block `C_1`:
        * `C_1 = Encrypt(Key, P_1 XOR IV)`
    5.  Calculate subsequent ciphertext blocks `C_i` (for `i > 1`):
        * `C_i = Encrypt(Key, P_i XOR C_{i-1})`
    6.  The final ciphertext is `C_1 || C_2 || ... || C_n`.

* **Decryption Process:**
    1.  Use the *same* Key and the *original IV*.
    2.  Split ciphertext `C` into blocks `C_1, C_2, ..., C_n`.
    3.  Calculate plaintext block `P_1`:
        * `P_1 = Decrypt(Key, C_1) XOR IV`
    4.  Calculate subsequent plaintext blocks `P_i` (for `i > 1`):
        * `P_i = Decrypt(Key, C_i) XOR C_{i-1})`
    5.  Concatenate plaintext blocks: `P_padded = P_1 || P_2 || ... || P_n`.
    6.  Remove the padding from `P_padded` to get the original plaintext `P`.

* **Function Logic:**
    * `encrypt_cbc(key, plaintext)`: Takes key/plaintext, generates random IV, pads, encrypts, returns `(iv, ciphertext)`.
    * `decrypt_cbc(key, iv, ciphertext)`: Takes key/iv/ciphertext, decrypts, unpads, handles `ValueError` for padding/decryption errors, returns `plaintext`.
* **Inputs/Outputs:** Functions take/return bytes; IV/Nonce are handled as bytes.

#### CTR Mode Explanation

Counter mode turns a block cipher (AES) into a stream cipher. It encrypts a sequence of counter values (combined with a Nonce) to generate a keystream, which is then XORed with the plaintext/ciphertext.

* **Nonce:** A unique value for each message encrypted with the same key. It doesn't need to be secret or random, but *must not be reused* with the same key. Using a random nonce is the easiest way to ensure uniqueness.
* **Counter:** An incrementing value, combined with the nonce for each block. The library handles counter incrementing internally.
* **Padding:** Not required for CTR mode.

* **Encryption/Decryption Process:**
    1.  Generate a unique (random recommended) Nonce (16 bytes).
    2.  Initialize a Counter (usually starts at 0 or 1).
    3.  For each plaintext block `P_i`:
        * Generate the input block for AES: `Input_Block_i = Nonce || Counter_i`
        * Encrypt the input block: `Keystream_Block_i = Encrypt(Key, Input_Block_i)`
        * Calculate ciphertext block: `C_i = P_i XOR Keystream_Block_i`
        * Increment `Counter_i`.
    4.  Decryption is the identical process: `P_i = C_i XOR Keystream_Block_i`.

* **Function Logic:**
    * `encrypt_ctr(key, plaintext)`: Takes key/plaintext, generates random Nonce, encrypts (no padding), returns `(nonce, ciphertext)`.
    * `decrypt_ctr(key, nonce, ciphertext)`: Takes key/nonce/ciphertext, decrypts (same operation as encrypt), returns `plaintext`.
* **Inputs/Outputs:** Functions take/return bytes; Nonce handled as bytes.

#### Main Block (`if __name__ == "__main__":`)

* Generates a single 256-bit AES key used for all demos in that run.
* Executes the CBC encryption/decryption example on two sample messages, verifying the results.
* Executes the CTR encryption/decryption example on two sample messages, verifying the results.

---

### `openssl_commands.sh`

* **Purpose:** Demonstrates command-line file encryption and decryption using `openssl enc` with AES-256-CBC mode, deriving the key from a password.
* **Key Concepts:** Password-Based Encryption, PBKDF2 (Password-Based Key Derivation Function 2), Salting, `openssl enc` command.

* **Step-by-step Logic:**
    1.  **Setup:** Defines filenames and a password variable. Creates a sample plaintext file (`sample_transaction_enc.txt`).
    2.  **Encryption:**
        * Runs `openssl enc -aes-256-cbc -salt -pbkdf2 -in ... -out ... -pass ...`.
        * `-salt`: Uses a random salt (stored in output file header) with the password.
        * `-pbkdf2`: Uses PBKDF2 to derive the key/IV from the password+salt.
        * Outputs binary ciphertext (`sample_transaction_enc.bin`).
    3.  **Base64 (Optional):** Shows conversion to/from Base64 text format using `openssl base64`.
    4.  **Decryption:**
        * Runs `openssl enc -d -aes-256-cbc -pbkdf2 -in ... -out ... -pass ...`.
        * `-d`: Decrypt mode.
        * Requires the *same password and options* (`-pbkdf2`). OpenSSL reads the salt from the input file to correctly re-derive the key/IV.
        * Outputs decrypted plaintext (`sample_transaction_enc_decrypted.txt`).
    5.  **Verification:** Uses `diff` to check if the decrypted file matches the original.
    6.  **Cleanup:** Reminds the user which files were created.

* **Inputs/Outputs:** Input plaintext file, password. Output ciphertext file (binary, optionally Base64), decrypted plaintext file.

---

### `openssl_cms_commands.sh`

* **Purpose:** Demonstrates command-line encryption (enveloping) and decryption using the Cryptographic Message Syntax (CMS) standard via `openssl cms`, typically involving public/private key pairs and certificates.
* **Key Concepts:** CMS, Public-Key Cryptography (Asymmetric), X.509 Certificates, Public/Private Keys, Hybrid Encryption (Enveloping).

* **Step-by-step Logic:**
    1.  **Setup:** Defines filenames for keys, certificates, and data.
    2.  **Key/Cert Generation (Conditional):** If key/cert files don't exist, it generates:
        * An RSA private key (`openssl genpkey`).
        * A self-signed X.509 certificate containing the corresponding public key (`openssl req`, `openssl x509`). This simulates having a recipient's certificate.
    3.  **Create Plaintext:** Creates a sample plaintext file (`plaintext_cms.txt`).
    4.  **Encryption (Enveloping):**
        * Runs `openssl cms -encrypt -recip <cert_file> -aes256 -in ... -out ...`.
        * Uses the recipient's certificate (`-recip`) to get their *public key*.
        * Generates a *random symmetric key* (AES-256), encrypts the data with it.
        * Encrypts the *symmetric key* with the recipient's *public key*.
        * Bundles both into the CMS output file (`enveloped_cms.pem`).
    5.  **Decryption:**
        * Runs `openssl cms -decrypt -inkey <private_key_file> -recip <cert_file> -in ... -out ...`.
        * Requires the recipient's *private key* (`-inkey`) to decrypt the bundled symmetric key.
        * Uses the recovered symmetric key to decrypt the data.
        * Outputs decrypted plaintext (`decrypted_cms.txt`).
    6.  **Verification:** Uses `diff` to check if the decrypted file matches the original.
    7.  **Cleanup:** Reminds the user which files were created (including key/cert).

* **Inputs/Outputs:** Input plaintext file, recipient certificate (for encryption), recipient private key (for decryption). Output CMS enveloped file, decrypted plaintext file. Generates key/certificate files if needed.

---

## Security Considerations

* **Key Management:** These examples generate keys/passwords insecurely for demonstration. Real applications require robust, secure key generation, storage, and management. Never hardcode keys or passwords in production code.
* **Randomness:** The security of CBC (IV) and CTR (Nonce) heavily relies on the unpredictability/uniqueness of the IV/Nonce generated for each encryption with the same key. `os.urandom()` is suitable for this.
* **Scope:** This project focuses only on the encryption/decryption mechanisms, not on building secure communication protocols or blockchain systems.