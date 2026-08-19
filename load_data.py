"""
Load ONGC NPT Workshop Dataset from Excel into SQLite database.
"""
import pandas as pd
import sqlite3
import os

EXCEL_PATH = r"Copy of ONGC_NPT_Workshop_Dataset.xlsx"
DB_PATH = r"npt_dashboard.db"

def load_data():
    # Read the NPT_Data sheet (header is on row 3, 0-indexed row 2)
    df = pd.read_excel(EXCEL_PATH, sheet_name="NPT_Data", header=2)
    
    # Clean column names
    df.columns = [
        "date", "rig_name", "well_name", "contractor",
        "npt_hours", "cause_category", "cause_detail",
        "drilling_phase", "month", "month_num"
    ]
    
    # Convert date to string for SQLite
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    
    # Remove any fully empty rows
    df = df.dropna(subset=["date", "rig_name", "npt_hours"])
    
    # Create SQLite DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Create table
    conn.execute("""
        CREATE TABLE npt_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            rig_name TEXT,
            well_name TEXT,
            contractor TEXT,
            npt_hours REAL,
            cause_category TEXT,
            cause_detail TEXT,
            drilling_phase TEXT,
            month TEXT,
            month_num INTEGER
        )
    """)
    
    # Insert data
    df.to_sql("npt_events", conn, if_exists="append", index=False)
    
    print(f"Loaded {len(df)} records into {DB_PATH}")
    
    # Verify
    cursor = conn.execute("SELECT COUNT(*) FROM npt_events")
    print(f"DB contains {cursor.fetchone()[0]} records")
    
    conn.close()

if __name__ == "__main__":
    load_data()
