import streamlit as st
import os
import sqlite3
import base64
from database import DB_PATH, init_db
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_encryption_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_file(file_path: str, password: str) -> bytes:
    with open(file_path, "rb") as f:
        data = f.read()
    
    salt = os.urandom(16)
    key = get_encryption_key(password, salt)
    f = Fernet(key)
    encrypted_data = f.encrypt(data)
    
    # Prepend salt to the encrypted data so we can extract it for decryption
    return salt + encrypted_data

def decrypt_data(encrypted_content: bytes, password: str) -> bytes:
    try:
        salt = encrypted_content[:16]
        actual_encrypted_data = encrypted_content[16:]
        
        key = get_encryption_key(password, salt)
        f = Fernet(key)
        decrypted_data = f.decrypt(actual_encrypted_data)
        return decrypted_data
    except Exception as e:
        raise ValueError("Invalid password or corrupted file.")

def render():
    st.header("💾 Data Refactory Center")
    st.write("Manage your complete application database. You can export secure backups, import data, or completely erase the system.")
    
    tab1, tab2, tab3 = st.tabs(["Erase Data", "Export Data", "Import Data"])
    
    with tab1:
        st.subheader("⚠️ Completely Erase All Data")
        st.warning("This action is IRREVERSIBLE. It will delete all students, programs, scores, and settings, returning the application to a blank state.")
        
        confirm_text = st.text_input("Type 'ERASE' to confirm deletion:", key="erase_confirm")
        
        if st.button("Delete All Data", type="primary", disabled=(confirm_text != "ERASE")):
            try:
                # Disconnect any open connections, then drop tables and reinit
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                # Get all tables
                c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = c.fetchall()
                for table_name in tables:
                    if table_name[0] != "sqlite_sequence":
                        c.execute(f"DROP TABLE IF EXISTS {table_name[0]}")
                conn.commit()
                conn.close()
                
                # Reinitialize DB structure and default seeds
                init_db()
                
                st.success("All data has been successfully erased and the database was re-initialized.")
            except Exception as e:
                st.error(f"Error erasing data: {e}")

    with tab2:
        st.subheader("🔒 Export Secure Backup")
        st.info("Your database file will be encrypted using the password provided below. Keep this password safe, you cannot import the file without it!")
        
        export_pass = st.text_input("Encryption Password (Optional but recommended)", type="password", key="export_pass")
        export_pass_confirm = st.text_input("Confirm Password", type="password", key="export_pass_confirm")
        
        if export_pass != export_pass_confirm:
            st.error("Passwords do not match!")
        else:
            if st.button("Generate Backup"):
                if not os.path.exists(DB_PATH):
                    st.error("Database file not found.")
                else:
                    try:
                        # Use password or default empty string for no password
                        pwd_to_use = export_pass if export_pass else "default_no_password_backup"
                        encrypted_bytes = encrypt_file(DB_PATH, pwd_to_use)
                        
                        st.success("Backup generated successfully! Click below to download.")
                        st.download_button(
                            label="Download Encrypted Backup (.enc)",
                            data=encrypted_bytes,
                            file_name="sports_manager_backup.enc",
                            mime="application/octet-stream"
                        )
                    except Exception as e:
                        st.error(f"Error generating backup: {e}")

    with tab3:
        st.subheader("📥 Import Data")
        st.error("WARNING: Importing a backup will completely overwrite your existing database. Any unsaved changes will be lost.")
        
        uploaded_file = st.file_uploader("Upload Backup File (.enc)", type=["enc"])
        import_pass = st.text_input("Decryption Password (leave blank if none was set)", type="password", key="import_pass")
        
        if uploaded_file is not None:
            if st.button("Decrypt and Import Backup", type="primary"):
                try:
                    file_content = uploaded_file.read()
                    pwd_to_use = import_pass if import_pass else "default_no_password_backup"
                    
                    decrypted_bytes = decrypt_data(file_content, pwd_to_use)
                    
                    # Verify it looks like a SQLite DB
                    if not decrypted_bytes.startswith(b"SQLite format 3\x00"):
                        st.error("Decrypted file is not a valid SQLite database! Decryption may have failed or file is corrupted.")
                    else:
                        # Backup the current DB just in case? Maybe too complicated, let's just overwrite.
                        with open(DB_PATH, "wb") as f:
                            f.write(decrypted_bytes)
                        
                        st.success("Database successfully imported! Please refresh the page or click to another tab to load the imported data.")
                except ValueError as ve:
                    st.error("Failed to decrypt: Incorrect password or corrupted file.")
                except Exception as e:
                    st.error(f"An unexpected error occurred during import: {e}")
