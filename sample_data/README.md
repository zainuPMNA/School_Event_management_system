# Sample Data (randomly generated, for testing only)

All names are random. Houses are **Group A / B / C** and categories/genders match the app's default Settings.

## Option A: Load a complete demo in one step
`demo_full_backup.enc` contains a fully set-up event:

| What | Amount |
|---|---|
| Students (with chest numbers 100+, 200+, 300+) | 120 |
| Sports programs / Arts programs | 54 / 44 |
| Individual assignments / group team members | 350 / 198 |
| Programs already scored (Sports / Arts) | 30 / 29, about 60%, so some are still pending |
| Schedule | 10–11 Dec 2026 (Sports), 12–13 Dec 2026 (Arts), no venue clashes |

1. Open **💾 Data Refactory Center → Import Data**.
2. Upload `demo_full_backup.enc`.
3. Password: `demo1234`
4. Click **Decrypt and Import Backup**.

⚠️ This **replaces** the current data. The app saves a snapshot of your current data first, so you can bring it back from **Automatic Snapshots**.

## Option B: Test the upload screens with CSV files
In **📁 Upload & Manage Data**, use the **Bulk Upload** boxes:

1. `1_students.csv` → Students tab. Then click **Generate Chest Numbers**.
2. Switch the sidebar to **Sports** mode → upload `2_programs_sports.csv` in the Programs tab.
3. Switch to **Arts** mode → upload `3_programs_arts.csv` in the Programs tab.
4. Assign students to programs in the **Individual Assignation** tab, then enter scores.
