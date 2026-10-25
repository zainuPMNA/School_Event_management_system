import streamlit as st
import os
import sqlite3
import base64
from database import DB_PATH, init_db, snapshot_database
from views.ui import hero, require_admin
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Backups made by older versions without a password used this fixed key; still accepted on import.
LEGACY_DEFAULT_PASSWORD = "default_no_password_backup"


def get_encryption_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_bytes(data: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    key = get_encryption_key(password, salt)
    # Prepend salt to the encrypted data so we can extract it for decryption
    return salt + Fernet(key).encrypt(data)


def decrypt_data(encrypted_content: bytes, password: str) -> bytes:
    try:
        salt = encrypted_content[:16]
        key = get_encryption_key(password, salt)
        return Fernet(key).decrypt(encrypted_content[16:])
    except Exception:
        raise ValueError("Invalid password or corrupted file.")


def read_database_bytes() -> bytes:
    """Consistent copy of the live database (safe even while someone is saving)."""
    src = sqlite3.connect(DB_PATH)
    mem = sqlite3.connect(":memory:")
    try:
        src.backup(mem)
        return mem.serialize()
    finally:
        src.close()
        mem.close()


def render():
    hero("Data Refactory Center", "Encrypted backups, restore, and a clean slate for next year.", "💾")
    if not require_admin():
        return

    tab1, tab2, tab3, tab4 = st.tabs(["Export Data", "Import Data", "Automatic Snapshots", "Erase Data"])

    with tab1:
        st.subheader("🔒 Export Secure Backup")
        st.info("Your database is encrypted with the password below. Keep it safe — the backup cannot be opened without it.")

        export_pass = st.text_input("Encryption Password (min 6 characters)", type="password", key="export_pass")
        export_pass_confirm = st.text_input("Confirm Password", type="password", key="export_pass_confirm")

        if export_pass and export_pass != export_pass_confirm:
            st.error("Passwords do not match!")
        elif st.button("Generate Backup", type="primary", disabled=len(export_pass) < 6):
            try:
                encrypted_bytes = encrypt_bytes(read_database_bytes(), export_pass)
                st.success("Backup generated successfully! Click below to download.")
                st.download_button(
                    label="Download Encrypted Backup (.enc)",
                    data=encrypted_bytes,
                    file_name="sports_manager_backup.enc",
                    mime="application/octet-stream"
                )
            except Exception as e:
                st.error(f"Error generating backup: {e}")

    with tab2:
        st.subheader("📥 Import Data")
        st.warning("Importing a backup replaces your current data. A snapshot of the current database is saved automatically "
                   "first (see **Automatic Snapshots**), so you can undo this.")

        uploaded_file = st.file_uploader("Upload Backup File (.enc)", type=["enc"])
        import_pass = st.text_input("Decryption Password (leave blank for old backups made without one)", type="password", key="import_pass")

        if uploaded_file is not None and st.button("Decrypt and Import Backup", type="primary"):
            try:
                decrypted_bytes = decrypt_data(uploaded_file.read(), import_pass or LEGACY_DEFAULT_PASSWORD)
                if not decrypted_bytes.startswith(b"SQLite format 3\x00"):
                    st.error("Decrypted file is not a valid SQLite database! Decryption may have failed or file is corrupted.")
                else:
                    snap = snapshot_database("before_import")
                    with open(DB_PATH, "wb") as f:
                        f.write(decrypted_bytes)
                    init_db()  # upgrade older backups to the current structure
                    st.success(f"Database imported! Previous data was saved to `{snap}`.")
                    st.balloons()
            except ValueError:
                st.error("Failed to decrypt: Incorrect password or corrupted file.")
            except Exception as e:
                st.error(f"An unexpected error occurred during import: {e}")

    with tab3:
        st.subheader("🕒 Automatic Snapshots")
        st.markdown("A copy of the database is saved in the `backups/` folder before every import or erase. Restore one if something went wrong.")
        snaps = sorted([f for f in os.listdir("backups") if f.endswith(".db")], reverse=True) if os.path.isdir("backups") else []
        if not snaps:
            st.info("No snapshots yet.")
        else:
            choice = st.selectbox("Snapshot", snaps)
            confirm = st.checkbox(f"Yes, replace the current data with **{choice}**")
            if st.button("Restore Snapshot", disabled=not confirm):
                snapshot_database("before_restore")
                src = sqlite3.connect(os.path.join("backups", choice))
                dst = sqlite3.connect(DB_PATH)
                try:
                    src.backup(dst)
                finally:
                    src.close()
                    dst.close()
                init_db()
                st.success("Snapshot restored!")

    with tab4:
        st.subheader("⚠️ Completely Erase All Data")
        st.warning("This deletes all students, programs, scores and settings and returns the app to a blank state. "
                   "A snapshot is saved to `backups/` first.")

        confirm_text = st.text_input("Type 'ERASE' to confirm deletion:", key="erase_confirm")

        if st.button("Delete All Data", type="primary", disabled=(confirm_text != "ERASE")):
            try:
                snap = snapshot_database("before_erase")
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                tables = c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
                for (table_name,) in tables:
                    if table_name != "sqlite_sequence":
                        c.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                conn.close()
                init_db()
                st.session_state["is_admin"] = False
                st.success(f"All data erased and the database re-initialized. A snapshot was saved to `{snap}`.")
            except Exception as e:
                st.error(f"Error erasing data: {e}")
