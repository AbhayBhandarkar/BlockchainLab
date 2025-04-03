# secure_crypto.py
# Implements secure AES-CBC and AES-CTR encryption/decryption
# Uses random IV/Nonce per message and handles padding errors via ValueError

import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
# Note: InvalidPadding import removed for compatibility, using ValueError instead.

# Use a secure backend
backend = default_backend()
# AES block size is 16 bytes (128 bits)
AES_BLOCK_SIZE_BYTES = algorithms.AES.block_size // 8

# --- AES-CBC Functions (Secure: Random IV per encryption) ---

def encrypt_cbc(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """
    Encrypts plaintext using AES-CBC with a securely generated random IV.
    Args: key (bytes), plaintext (bytes) Returns: tuple (iv, ciphertext)
    """
    if len(key) not in [16, 24, 32]:
         raise ValueError("Invalid AES key size. Must be 16, 24, or 32 bytes.")
    iv = os.urandom(AES_BLOCK_SIZE_BYTES) # Fresh random IV
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv, ciphertext

def decrypt_cbc(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """
    Decrypts AES-CBC ciphertext. Handles padding errors via ValueError.
    Args: key (bytes), iv (bytes), ciphertext (bytes) Returns: plaintext (bytes)
    """
    if len(key) not in [16, 24, 32]:
         raise ValueError("Invalid AES key size. Must be 16, 24, or 32 bytes.")
    if len(iv) != AES_BLOCK_SIZE_BYTES:
        raise ValueError(f"Invalid IV size. Must be {AES_BLOCK_SIZE_BYTES} bytes.")

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    try:
        decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        return plaintext
    except ValueError as e:
        # Catches potential decryption or unpadding errors, including padding errors
        # which often raise ValueError (especially in older library versions).
        print(f"Decryption or Unpadding error (ValueError): {e}")
        raise # Re-raise the exception

# --- AES-CTR Functions (Secure: Unique Nonce per encryption) ---

def encrypt_ctr(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """
    Encrypts plaintext using AES-CTR with a securely generated random nonce.
    Args: key (bytes), plaintext (bytes) Returns: tuple (nonce, ciphertext)
    """
    if len(key) not in [16, 24, 32]:
         raise ValueError("Invalid AES key size. Must be 16, 24, or 32 bytes.")
    nonce = os.urandom(AES_BLOCK_SIZE_BYTES) # Fresh random nonce
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=backend)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize() # No padding needed
    return nonce, ciphertext

def decrypt_ctr(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """
    Decrypts AES-CTR ciphertext.
    Args: key (bytes), nonce (bytes), ciphertext (bytes) Returns: plaintext (bytes)
    """
    if len(key) not in [16, 24, 32]:
         raise ValueError("Invalid AES key size. Must be 16, 24, or 32 bytes.")
    if len(nonce) != AES_BLOCK_SIZE_BYTES:
         raise ValueError(f"Invalid Nonce size. Must be {AES_BLOCK_SIZE_BYTES} bytes.")

    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=backend)
    decryptor = cipher.decryptor() # CTR decryption is same operation as encryption
    try:
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext
    except ValueError as e:
        print(f"Decryption error: {e}")
        raise

# --- Example Usage ---
if __name__ == "__main__":
    print(f"Running crypto examples on: {os.uname()}") # Show OS info
    print(f"Current Time (approx): Thursday, April 3, 2025 at 9:55 AM IST") # Add context
    # Generate a strong key ONCE (e.g., 256-bit / 32 bytes)
    aes_key = os.urandom(32)
    print(f"Using AES Key (hex): {aes_key.hex()}")

    # --- CBC Example ---
    print("\n" + "="*10 + " Secure CBC Example " + "="*10)
    tx_data_cbc1 = b"TX_CBC_1: Sender: Alice, Receiver: Bob, Amount: 10 BTC, Date: 2025-04-03"
    print(f"Original CBC TX 1: {tx_data_cbc1.decode()}")
    iv1, cipher_cbc1 = encrypt_cbc(aes_key, tx_data_cbc1)
    print(f"IV 1 (hex): {iv1.hex()}")
    print(f"Ciphertext CBC 1 (hex): {cipher_cbc1.hex()}")

    tx_data_cbc2 = b"TX_CBC_2: Sender: Charlie, Receiver: David, Amount: 5 ETH, Date: 2025-04-03"
    print(f"\nOriginal CBC TX 2: {tx_data_cbc2.decode()}")
    iv2, cipher_cbc2 = encrypt_cbc(aes_key, tx_data_cbc2)
    print(f"IV 2 (hex): {iv2.hex()}")
    print(f"Ciphertext CBC 2 (hex): {cipher_cbc2.hex()}")

    # Decrypt ("Receiver End")
    try:
        decrypted_cbc1 = decrypt_cbc(aes_key, iv1, cipher_cbc1)
        print(f"\nDecrypted CBC TX 1: {decrypted_cbc1.decode()}")
        assert tx_data_cbc1 == decrypted_cbc1
        print("CBC Message 1 verified.")

        decrypted_cbc2 = decrypt_cbc(aes_key, iv2, cipher_cbc2)
        print(f"Decrypted CBC TX 2: {decrypted_cbc2.decode()}")
        assert tx_data_cbc2 == decrypted_cbc2
        print("CBC Message 2 verified.")
    except Exception as e: # Catch broader errors during demo
        print(f"CBC Decryption/Verification Failed: {e}")

    # --- CTR Example ---
    print("\n" + "="*10 + " Secure CTR Example " + "="*10)
    tx_data_ctr1 = b"TX_CTR_1: Action: Stake, Amount: 1000 ADA, Date: 2025-04-03"
    print(f"Original CTR TX 1: {tx_data_ctr1.decode()}")
    nonce1, cipher_ctr1 = encrypt_ctr(aes_key, tx_data_ctr1)
    print(f"Nonce 1 (hex): {nonce1.hex()}")
    print(f"Ciphertext CTR 1 (hex): {cipher_ctr1.hex()}")

    tx_data_ctr2 = b"TX_CTR_2: Action: Vote, ProposalID: 123, Choice: Yes, Date: 2025-04-03"
    print(f"\nOriginal CTR TX 2: {tx_data_ctr2.decode()}")
    nonce2, cipher_ctr2 = encrypt_ctr(aes_key, tx_data_ctr2)
    print(f"Nonce 2 (hex): {nonce2.hex()}")
    print(f"Ciphertext CTR 2 (hex): {cipher_ctr2.hex()}")

    # Decrypt ("Receiver End")
    try:
        decrypted_ctr1 = decrypt_ctr(aes_key, nonce1, cipher_ctr1)
        print(f"\nDecrypted CTR TX 1: {decrypted_ctr1.decode()}")
        assert tx_data_ctr1 == decrypted_ctr1
        print("CTR Message 1 verified.")

        decrypted_ctr2 = decrypt_ctr(aes_key, nonce2, cipher_ctr2)
        print(f"Decrypted CTR TX 2: {decrypted_ctr2.decode()}")
        assert tx_data_ctr2 == decrypted_ctr2
        print("CTR Message 2 verified.")
    except Exception as e: # Catch broader errors during demo
        print(f"CTR Decryption/Verification Failed: {e}")

    print("\n" + "="*10 + " Python Examples Complete " + "="*10)