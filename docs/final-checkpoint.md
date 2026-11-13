# CSMS Final Development Checkpoint

## 1. DEVELOPER INFORMATION
- **Name:** Jhoanna Delapaz
- **GitHub Username:** `jhoanna-delapaz`
- **Technology Stack:** Python 3.13+, Flask 3.1, pytest, SQLite
- **T16 Branch:** `feature/t16-final-release`
- **Final Release Version:** `1.0.0`

---

## 2. MY FINAL RELEASE IMPLEMENTATION
I established the official `1.0.0` release version in `BaseConfig.APP_VERSION` inside `src/csms/config.py`, with matching package metadata in `pyproject.toml`. Placing `APP_VERSION` in `BaseConfig` fits the application's layered Flask architecture because configuration settings act as a shared foundation across all environments without mixing metadata into business logic or database code. The `/health` route reads `APP_VERSION` and `APP_NAME` directly from Flask's `current_app.config` and returns them in its JSON status without exposing any sensitive keys or file paths. For the browser interface, the shared `navbar.html` template reads `config.APP_VERSION` through Jinja2's built-in Flask configuration context so every main page displays `v1.0.0` automatically. By deriving both the JSON endpoint and the HTML navigation badge from that single configuration attribute, I avoided duplicating hardcoded version strings across templates or routes. 

---

## 3. FILES I CHANGED
- **`src/csms/config.py`:** Updated `BaseConfig.APP_VERSION` from `"0.1.0"` to `"1.0.0"` to build a single authoritative source of truth for the official release version across the entire Flask application.
- **`pyproject.toml`:** Updated the project metadata `version` field from `"0.1.0"` to `"1.0.0"` so Python packaging metadata matches the application runtime version.
- **`src/csms/templates/navbar.html`:** Added a release version badge displaying `v{{ config.APP_VERSION }}` in the shared sticky navigation bar so `v1.0.0` appears consistently across Dashboard, Residents, and Service Requests views without redesigning the UI.
- **`tests/test_smoke.py`:** Updated the expected version assertion in `test_health_endpoint_returns_ok` from `"0.1.0"` to `"1.0.0"` so the baseline health smoke test verifies the official release version.

---

## 4. MY FINAL EXAMINATION TEST
- **Test Name:** `test_resident_service_request_lifecycle_and_dashboard_persistence` (`tests/test_final_release.py`)
- **Modules/Responsibilities Covered:**
  1. Resident Registration & SQLite Persistence (`ResidentRegistrationService`, `ResidentRepository`)
  2. Service Request Submission & Active-Resident Eligibility (`ServiceRequestSubmissionService`, `ServiceRequestRepository`)
  3. Controlled Service Request Status Workflow (`ServiceRequestStatusService`)
  4. Resident Deactivation  (`ResidentDeactivationService`)
  5. Operational Dashboard  (`DashboardService`)
- **Starting State:** A fresh, isolated temporary SQLite database (`tmp_path / "t16-final-release.sqlite"`), verified through `DashboardService.get_summary()` to start with `0` total residents and `0` total service requests.
- **Operations Performed:**
  1. Registered a new active resident and verified database persistence.
  2. Submitted two service requests for that active resident via `POST /service-requests/new` and confirmed both persisted with `"Pending"` status.
  3. Transitioned the first request forward through `Pending` -> `In Progress` -> `Completed` via `POST /service-requests/<id>/status`, then submitted an invalid backward transition (`Completed` -> `In Progress`) to verify terminal state is working.
  4. Deactivated the resident via `POST /residents/<id>/deactivate` and attempted to submit a third service request for the now-inactive resident via `POST /service-requests/new`.
  5. Queried `DashboardService.get_summary()` and inspected SQLite repositories directly to compare counts against persisted records.
- **Expected Final State:** The database contains `1` resident with `status == "Inactive"` and `2` service requests (`1` `"Completed"` and `1` `"Pending"`), the invalid backward transition and inactive-resident submission are both rejected without altering saved records, and `DashboardService.get_summary()` accurately reports `1` total resident, `0` active residents, `1` inactive resident, `2` total service requests, `1` open/pending request, `1` completed request, and `0` cancelled requests.
- **Why This Test Is Meaningful:** Isolated unit tests only check single functions in separation, which can miss bugs that happen when modules interact. By running real HTTP routes against a genuine SQLite database across five connected modules, and testing both valid and rejected cases, this integration test proves that domain rules, persistence, and Dashboard totals remain synchronized.
---

## 5. MY FINAL TECHNICAL DECISION
- **Decision:** Placed `v{{ config.APP_VERSION }}` inside the shared `src/csms/templates/navbar.html` partial template so the release version is rendered from Flask's `config` context on every main view.
- **Alternative Considered:** Hardcoding `v1.0.0` individually into each page template (`index.html`, `residents.html`, `service_requests.html`) or adding a separate API call to get`/health` on page load.
- **Reason for My Decision:** Since `navbar.html` is already included across the primary application views, referencing `config.APP_VERSION` in one shared template guaranteed consistent `v1.0.0` visibility everywhere, avoided duplicate hardcoded strings, and required zero extra network requests or UI redesign.

---

## 6. PROBLEM OR VERIFICATION ISSUE ENCOUNTERED
- **Problem:** After changing `BaseConfig.APP_VERSION` from `"0.1.0"` to `"1.0.0"`, `test_health_endpoint_returns_ok` in `tests/test_smoke.py` failed because it still asserted the starter `"0.1.0"` version.
- **Cause or Investigation:** Inspecting `tests/test_smoke.py` showed that `test_health_endpoint_returns_ok` directly checked `payload["version"] == "0.1.0"` I also checked the repository with `git grep "0.1.0"` to ensure no other files still referenced the old version.
- **Resolution:** Updated `test_health_endpoint_returns_ok` in `tests/test_smoke.py` to expect `"1.0.0"`, and verified that all smoke tests and release checks pass.
---

## 7. FINAL REGRESSION RESULTS
- **Test Command:** `python -m pytest`
- **T15 Baseline Tests:** `164` passing
- **T16 Final Release Tests Added (`tests/test_final_release.py`):** `3` passing (`test_health_endpoint_reports_final_release_version_safely`, `test_ui_views_display_consistent_release_version`, `test_resident_service_request_lifecycle_and_dashboard_persistence`)
- **Final Regression Run 1:** `167 passed in 71.24s (0:01:11)`, `0 failed`
- **Final Regression Run 2:** `167 passed in 70.51s (0:01:10)`, `0 failed`
- **Manual Acceptance Verification:** Confirmed smooth app startup, `/health` output, `v1.0.0` badge across pages, Resident actions, Service Request actions, and live Dashboard updates.

---

## 8. TOOLS AND REFERENCES USED
- **Git & GitHub:** Git CLI for feature branching, diffs, tagging (`v1.0.0`), and GitHub Pull Request and Release workflows.
- **IDE & AI Assistance:** Visual Studio Code for code editing and terminal execution, and an AI coding assistant used to review release requirements, structure integration test cases, and fix documentation formatting while I personally executed, debugged, and validated all code and tests.
---

## 9. FINAL RELEASE DECLARATION
CSMS v1.0.0 - READY FOR RELEASE