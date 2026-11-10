# CSMS Release-Readiness Report (T15 System Hardening & Regression Testing)

## 1. Developer Information
- **Developer Name:** Jhoanna Delapaz
- **GitHub Username:** jhoanna-delapaz
- **Technology Stack:** Python 3.13+, Flask 3.1, pytest, SQLite
- **T15 Feature Branch:** `feature/t15-system-hardening`

---

## 2. Release Candidate Baseline
Checked application status before starting T15 hardening:
- **Application Startup:** Working (PASS)
- **`/health` Endpoint:** Working (PASS)
- **Dashboard (`/dashboard`):** Working (PASS)
- **Resident Management (`/residents`):** Working (PASS)
- **Service Request Management (`/service-requests`):** Working (PASS)
- **Starter through T14 Automated Tests:** All 159 tests passed cleanly

---

## 3. Hardening Changes

| Area | Issue or Risk Found | Action Taken | Files Changed | Test/Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **1. Full Regression Behavior** | Reviewed - no defect identified. | Checked that past features work cleanly without breaking. | None | 159 baseline tests |
| **2. Invalid & Missing Input Handling** | Reviewed - no defect identified. | Checked that invalid text in page URLs returns a safe 404 error page. | `tests/test_t15_hardening.py` | `test_malformed_route_identifier_handled_safely` |
| **3. Persistence Integrity** | Reviewed - no defect identified. | Checked that rejected form updates do not change saved database records. | `tests/test_t15_hardening.py` | `test_rejected_invalid_resident_update_leaves_persistence_unchanged` |
| **4. HTTP & Mutation Safety** | Reviewed - no defect identified. | Checked that viewing pages does not save unwanted database changes. | `tests/test_t15_hardening.py` | `test_dashboard_get_does_not_mutate_persistence` |
| **5. Query & Database Safety** | Reviewed - no defect identified. | Checked that database search inputs use safe parameterized queries (`?`). | None | Database repository code audit |
| **6. Workflow & Lifecycle Protection** | Reviewed - no defect identified. | Checked that status flows correctly and inactive residents cannot submit requests. | `tests/test_t15_hardening.py` | `test_deactivated_resident_reflected_in_dashboard_and_blocks_submission` |
| **7. Interface & Navigation Consistency** | Reviewed - no defect identified. | Checked that page links and alert messages work across all screens. | None | Manual page verification |
 


---

## 4. Five New T15 Hardening Tests

### 1. `test_malformed_route_identifier_handled_safely`
- **Category:** Invalid or Malformed Input
- **What It Verifies:** Checks that typing invalid text into page URLs returns a 404 page instead of crashing the app.
- **Why It Adds Value:** Prevents unexpected server crashes on bad link requests.

### 2. `test_rejected_invalid_resident_update_leaves_persistence_unchanged`
- **Category:** Rejected Mutation Protects Persistence
- **What It Verifies:** Checks that submitting blank required fields keeps the saved database record untouched.
- **Why It Adds Value:** Keeps saved data safe when validation fails.

### 3. `test_dashboard_get_does_not_mutate_persistence`
- **Category:** Read-Only Request Safety
- **What It Verifies:** Checks that viewing the Dashboard multiple times does not add or alter database records.
- **Why It Adds Value:** Ensures browsing pages never changes saved data.

### 4. `test_deactivated_resident_reflected_in_dashboard_and_blocks_submission`
- **Category:** Cross-Feature Regression
- **What It Verifies:** Checks that deactivating a resident updates dashboard numbers and stops new request submissions.
- **Why It Adds Value:** Ensures resident status syncs correctly across the dashboard and request submission.

### 5. `test_recent_requests_boundary_strictly_respects_limit`
- **Category:** Repeatability or Boundary Behavior
- **What It Verifies:** Checks that the recent requests list shows a maximum of 5 items when more exist.
- **Why It Adds Value:** Keeps the dashboard layout within strict count limits.

---

## 5. Full Regression Test Results

- **Test Command Used:** `python -m pytest`
- **Regression Run 1 Result:** 164 passed in 67.62s (0:01:07) (0 failed)
- **Regression Run 2 Result:** 164 passed in 66.22s (0:01:06) (0 failed)
- **Total Passing Tests:** 164

---

## 6. Manual Release Verification

**Command used to start up the application:** flask --app csms run --debug

| Verification | Result | Notes |
| :--- | :---: | :--- |
| Application starts | **PASS** | App starts smoothly |
| `/health` works | **PASS** | Returns `{"status": "ok"}` |
| Dashboard loads | **PASS** | Displays summary boxes and recent requests table |
| Resident listing/search works | **PASS** | Finds residents by partial name search |
| Valid Resident registration works | **PASS** | Saves resident as Active with auto ID |
| Invalid Resident registration is rejected | **PASS** | Displays validation errors and does not save |
| Resident update works | **PASS** | Edits resident info without changing ID or status |
| Resident deactivation works and record remains visible | **PASS** | Changes status to Inactive while keeping record visible |
| Valid Service Request submission for Active Resident works | **PASS** | Submits new request under Pending status |
| Missing/Inactive Resident submission is rejected | **PASS** | Blocks submission and shows error message |
| Service Request search/filter/details work | **PASS** | Search bar, status dropdown, and detail views work |
| Valid Service Request workflow works | **PASS** | Moves status Pending -> In Progress -> Completed |
| Invalid/terminal transition is rejected | **PASS** | Blocks invalid status changes |
| Dashboard reflects Resident/Service Request changes | **PASS** | Numbers update right after data changes |
| Read-Only GET operations do not modify persistence | **PASS** | Page browsing leaves saved data unchanged |

---

## 7. Repository Hygiene Review
- **Debug output:** Checked and cleaned.
- **Temporary and empty files:** Removed.
- **Generated build/runtime artifacts:** Verified excluded via `.gitignore`.
- **Accidental local database files:** Verified production database path handled safely.
- **Commented-out abandoned code:** Audited and removed.
- **Secrets/credentials:** None hardcoded or committed.
- **Broken navigation/links:** All navbar and detail links verified.
- **Direct SQL parameter binding:** All queries use parameter binding (`?`).

---

## 8. Known Limitations
No known release-blocking limitations identified within the defined CSMS scope.

---

## 9. Release Candidate Statement

**READY FOR T16 FINAL EXAM**