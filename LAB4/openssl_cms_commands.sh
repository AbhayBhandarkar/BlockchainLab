#!/bin/bash

# openssl_cms_commands.sh
# Demonstrates basic encryption (enveloping) and decryption using OpenSSL CMS.

echo "--- OpenSSL CMS Encryption/Decryption Example ---"
echo "(Current Time: Approx Thursday, April 3, 2025 at 9:55 AM IST)"

# --- Configuration ---
KEY_FILE="receiver_cms_key.pem"
CERT_FILE="receiver_cms_cert.pem"
PLAINTEXT_FILE="plaintext_cms.txt"
ENVELOPED_FILE="enveloped_cms.pem" # Output of cms encrypt
DECRYPTED_FILE="decrypted_cms.txt" # Output of cms decrypt

# --- 1. Generate Recipient Key Pair and Certificate (Self-Signed) ---
if [ ! -f "$KEY_FILE" ] || [ ! -f "$CERT_FILE" ]; then
  echo -e "\n--- Generating Recipient Private Key and Self-Signed Certificate ---"
  openssl genpkey -algorithm RSA -out $KEY_FILE -pkeyopt rsa_keygen_bits:2048
  if [ $? -ne 0 ]; then echo "Error generating private key"; exit 1; fi
  echo "Generated private key: $KEY_FILE"
  openssl req -new -key $KEY_FILE -out temp_csr.pem -subj "/CN=TestCmsReceiver/O=Example/C=IN"
  if [ $? -ne 0 ]; then echo "Error generating CSR"; exit 1; fi
  openssl x509 -req -days 365 -in temp_csr.pem -signkey $KEY_FILE -out $CERT_FILE
  if [ $? -ne 0 ]; then echo "Error generating self-signed certificate"; exit 1; fi
  echo "Generated self-signed certificate: $CERT_FILE"
  rm temp_csr.pem # Clean up CSR
else
  echo -e "\n--- Using existing key ($KEY_FILE) and certificate ($CERT_FILE) ---"
fi

# --- 2. Create Sample Plaintext File ---
echo -e "\n--- Creating sample plaintext file: $PLAINTEXT_FILE ---"
echo "TX_OPENSSL_CMS: This data will be encrypted using OpenSSL CMS." > $PLAINTEXT_FILE
echo "RecipientID: TestCmsReceiver" >> $PLAINTEXT_FILE
echo "Timestamp: $(date --iso-8601=seconds)" >> $PLAINTEXT_FILE
cat $PLAINTEXT_FILE

# --- 3. Encrypt (Envelop) Data using CMS ---
echo -e "\n--- Encrypting (Enveloping) data with CMS for $CERT_FILE ---"
openssl cms -encrypt -in $PLAINTEXT_FILE -out $ENVELOPED_FILE -recip $CERT_FILE -aes256
if [ $? -eq 0 ]; then echo "Successfully enveloped data to $ENVELOPED_FILE"; ls -l $ENVELOPED_FILE; else echo "CMS Encryption failed!"; exit 1; fi

# --- 4. Decrypt Data using CMS ---
echo -e "\n--- Decrypting CMS enveloped data (openssl cms -decrypt) ---"
openssl cms -decrypt -in $ENVELOPED_FILE -out $DECRYPTED_FILE -recip $CERT_FILE -inkey $KEY_FILE
if [ $? -eq 0 ]; then echo "Successfully decrypted data to $DECRYPTED_FILE"; echo "Decrypted content:"; cat $DECRYPTED_FILE; else echo "CMS Decryption failed!"; exit 1; fi

# --- 5. Verification ---
echo -e "\n--- Verifying Decryption Result ---"
diff $PLAINTEXT_FILE $DECRYPTED_FILE
if [ $? -eq 0 ]; then echo "SUCCESS: Decrypted CMS content matches original plaintext."; else echo "FAILURE: Decrypted CMS content does NOT match original plaintext."; fi

# --- Cleanup ---
echo -e "\n--- Cleaning up temporary files ---"
# Uncomment the next line to automatically delete generated files
# rm -f $PLAINTEXT_FILE $ENVELOPED_FILE $DECRYPTED_FILE $KEY_FILE $CERT_FILE
echo "Cleanup command commented out. Files: $PLAINTEXT_FILE, $ENVELOPED_FILE, $DECRYPTED_FILE, $KEY_FILE, $CERT_FILE"

echo -e "\n--- OpenSSL CMS Example Finished ---"