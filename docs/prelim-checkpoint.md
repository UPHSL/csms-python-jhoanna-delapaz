# Developer Checkpoint: T03 Implementation

## Developer Information

* **Name:** Jhoanna Alexandra C. De La Paz
* **GitHub Username:** jhoanna-delapaz
* **Primary Technology Stack:** Python, SQLite, pytest
* **T03 Branch:** feature/t03-resident-repository

---

## My T03 Implementation

Resident data is stored in a file-backed SQLite database, initialized by my database schema code. I stored my database.py in a new separate folder called 'db' inside src to be neat, since I did not know where it could fit in the existing folders, plus the old github project had a separate 'data' folder for database files. The `ResidentRepository` class serves as the persistence layer that handles all database reads and writes. When saving a `Resident` object, the repository makes a SQLite connection and executes an `INSERT INTO` query using these placeholders (`?`) to safely store the attributes. SQLite automatically assigns a unique integer primary key to the new record, which the repository retrieves using `cursor.lastrowid` and assigns back to the `Resident.id` property. To retrieve a resident, the repository runs a `SELECT` query using `find_by_id(resident_id)`. If the specified resident exists, it turns the raw database row into a `Resident` Python object. If the ID does not exist, `find_by_id` returns `None` safely without any errors or crashes.

---

## My Persistence Design Decision

* **What I Decided:**  
  I used ? placeholders in my SQL queries and manually mapped database rows into Resident objects.

* **Why I Implemented It That Way:**  
  The ? placeholders treats input strictly as plain data, not executable SQL code. Mapping rows manually keeps the code simple and ensures the app returns None instead of crashing when a resident isn't found.


---

## Files I Changed

* **File:** `.gitignore`  
  **Purpose:** Added extra ignore patterns to prevent temporary SQLite database files (`*.db`) and Python cache files from being tracked by Git.

* **File:** `src/csms/repositories/resident_repository.py`  
  **Purpose:** Implements the `ResidentRepository` class, providing the persistence methods (`save` and `find_by_id`) to interact directly with SQLite tables.

* **File:** `tests/test_resident_repository.py`  
  **Purpose:** Stores the automated unit tests written with `pytest` and `tmp_path` fixtures to verify that resident creation, unique ID assignment, and retrieval work across isolated test databases.

---

## Problem I Encountered

* **Problem or error:** The find_by_id method crashed whenever I tried to search for a resident ID that didn't exist in the database.
* **Cause:** When an ID is not found, cursor.fetchone() returns None. It caused Python to throw an error because you can't read fields from None.
* **How I resolved it:** I added a check (if row is None: return None) right after running the query. If the row doesn't exist, it stops early and safely returns None.

---

## My Student-Designed Test

* **Test name:** `test_sequential_residents_get_unique_ids`
* **What it verifies:** It ensures that saving multiple residents sequentially in the same database instance generates unique, auto-incrementing primary key IDs.
* **Why I chose this scenario:** The given standard tests only evaluate saving a single resident in an isolated database. I chose this scenario to ensure that sequential inserts do not accidentally overwrite existing records or cause ID collision errors.

---

## Tools and References Used

* **Course guide / Instructions:** Provided requirements for T03, required test scenarios, and out-of-scope boundaries. 
* **Old Projects:** Read past database projects for coding reference.
* **pytest Documentation:** Reference for the `tmp_path` fixture concept: https://docs.pytest.org/en/stable/how-to/tmp_path.html
* **AI / Coding Assistant (Gemini):** Assisted in setting up test structure, repository code, debugging and explaining many unfamiliar concepts like `typing.Optional` and `find_by_id` logic.