#!/bin/bash

# openssl_commands.sh
# Demonstrates AES encryption, encoding, decoding, and decryption using OpenSSL enc

echo "--- OpenSSL 'enc' AES-256-CBC Example ---"
echo "(Current Time: Approx Thursday, April 3, 2025 at 9:55 AM IST)"

# --- Configuration ---
FILENAME="sample_transaction_enc.txt"
CIPHER_BIN="sample_transaction_enc.bin"
CIPHER_B64="sample_transaction_enc.b64"
DECODED_BIN="sample_transaction_enc_decoded.bin" # Temp file if using base64
DECRYPTED_TXT="sample_transaction_enc_decrypted.txt"
PASSWORD="your_secret_password_123!" # Use a strong, securely managed password/key in reality

# --- Setup ---
echo -e "\n--- Creating sample plaintext file: $FILENAME ---"
echo "TX_OPENSSL_ENC: Sender: Alice, Receiver: Bob, Amount: 1 BTC" > $FILENAME
echo "Timestamp: $(date --iso-8601=seconds)" >> $FILENAME
cat $FILENAME
echo "Using password (for demonstration): [HIDDEN]"


# --- Encryption ---
echo -e "\n--- Encrypting with AES-256-CBC (openssl enc) ---"
openssl enc -aes-256-cbc -salt -pbkdf2 -in $FILENAME -out $CIPHER_BIN -pass pass:$PASSWORD
if [ $? -eq 0 ]; then echo "Successfully encrypted $FILENAME to $CIPHER_BIN"; ls -l $CIPHER_BIN; else echo "Encryption failed!"; exit 1; fi

# --- Encoding (Optional) ---
echo -e "\n--- Base64 Encoding Ciphertext (Optional) ---"
openssl base64 -in $CIPHER_BIN -out $CIPHER_B64
if [ $? -eq 0 ]; then echo "Successfully Base64 encoded $CIPHER_BIN to $CIPHER_B64"; ls -l $CIPHER_B64; else echo "Base64 encoding failed!"; fi

# --- Decoding (Optional - only if encoded) ---
if [ -f $CIPHER_B64 ]; then
    echo -e "\n--- Base64 Decoding Ciphertext (If Encoded) ---"
    openssl base64 -d -in $CIPHER_B64 -out $DECODED_BIN
    if [ $? -eq 0 ]; then echo "Successfully Base64 decoded $CIPHER_B64 to $DECODED_BIN"; ls -l $DECODED_BIN; else echo "Base64 decoding failed! Will attempt to decrypt original binary."; rm -f $DECODED_BIN; fi
fi

# --- Decryption ---
echo -e "\n--- Decrypting Ciphertext (openssl enc -d) ---"
DECRYPT_SOURCE_FILE=$CIPHER_BIN # Default to original binary
if [ -f $DECODED_BIN ]; then
   # You could use the decoded file if preferred and it exists
   # DECRYPT_SOURCE_FILE=$DECODED_BIN
   echo "(Note: Decrypting from original binary $CIPHER_BIN)"
fi
openssl enc -d -aes-256-cbc -pbkdf2 -in $DECRYPT_SOURCE_FILE -out $DECRYPTED_TXT -pass pass:$PASSWORD
if [ $? -eq 0 ]; then echo "Successfully decrypted $DECRYPT_SOURCE_FILE to $DECRYPTED_TXT"; echo "Decrypted content:"; cat $DECRYPTED_TXT; else echo "Decryption failed!"; exit 1; fi

# --- Verification ---
echo -e "\n--- Verifying Decryption Result ---"
diff $FILENAME $DECRYPTED_TXT
if [ $? -eq 0 ]; then echo "SUCCESS: Decrypted content matches original plaintext."; else echo "FAILURE: Decrypted content does NOT match original plaintext."; fi

# --- Cleanup ---
echo -e "\n--- Cleaning up temporary files ---"
# Uncomment the next line to automatically delete generated files
# rm -f $FILENAME $CIPHER_BIN $CIPHER_B64 $DECODED_BIN $DECRYPTED_TXT
echo "Cleanup command commented out. Files: $FILENAME, $CIPHER_BIN, $CIPHER_B64, $DECODED_BIN, $DECRYPTED_TXT"

echo -e "\n--- OpenSSL 'enc' Example Finished ---"