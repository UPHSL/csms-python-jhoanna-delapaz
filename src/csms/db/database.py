"""
This section/module connects to SQLite, ensures the residents 
table exists before tries to read or write data.
"""
import sqlite3


def init_db(db_path: str = "csms.db") -> None:
    """Sets up the SQLite database and creates the residents table if it's missing."""
    # Connect to the SQLite database file (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the residents table with the needed data types
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS residents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            address TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """
    )

    # Save changes and close connection
    conn.commit()
    conn.close()