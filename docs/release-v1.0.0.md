# CSMS v1.0.0 Official Release Notes & System Documentation

## 1. Release Overview
- **Application Name:** Community Services Management System (CSMS)
- **Official Release Version:** `1.0.0`
- **Release Date:** November 13, 2026
- **Technology Stack:** Python 3.13+, Flask 3.1, pytest, SQLite
- **Release Type:** Final Course Release

---

## 2. Implemented Feature Summary (T01–T16)
- **System Setup & Health Check (T01–T02):** Set up the Flask app (`create_app`), shared settings (`BaseConfig`), SQLite table setup (`init_db`), and the `/health` endpoint showing the app name, status, and version `1.0.0`.
- **Resident Management (T03–T07, T12):** Built the `Resident` model, input checks, safe SQLite database queries (`ResidentRepository`), active resident registration, name search, profile editing (without changing ID or status), and resident deactivation (`Active` -> `Inactive`).
- **Service Request Workflow (T08–T11, T13):** Built the `ServiceRequest` model, input checks, safe SQLite database queries (`ServiceRequestRepository`), rules blocking missing or inactive residents from submitting requests, search and status filters, detail pages, and step-by-step status updates (`Pending` -> `In Progress` -> `Completed` / `Cancelled`) that block invalid changes.
- **Dashboard Summary (T14):** Built `DashboardService` and the Dashboard page to show total, active, and inactive resident counts; service request counts by status; and the 5 newest service requests.
- **System Hardening & Final Release (T15–T16):** Tested bad URLs, checked that failed updates do not change saved records, added consistent `v1.0.0` version labels across `/health` and all pages, and verified the full workflow with a real SQLite database.

---

## 3. Architecture Summary
CSMS is organized into clear layers so each part has one job:
- **Web & Pages (`src/csms/ui/`, `src/csms/templates/`):** Flask routes and HTML templates that handle browser requests, show forms and messages, and display `v1.0.0` in the top navigation bar (`navbar.html`).
- **Business Logic (`src/csms/services/`):** Holds the app rules: checking required fields, making sure only active residents can submit requests, controlling status steps, and counting Dashboard totals.
- **Data Models (`src/csms/models/`):** Simple Python classes (`Resident`, `ServiceRequest`, `DashboardSummary`) that represent the main records in the system.
- **Database Storage (`src/csms/repositories/`, `src/csms/db/`):** Creates the SQLite tables and runs safe parameterized SQL (`?`) queries to save and load data.
- **App Settings (`src/csms/config.py`):** Stores `BaseConfig.APP_VERSION = "1.0.0"` and `BaseConfig.APP_NAME` in one central place used by both `/health` and the web pages.

---

## 4. Setup & Run Instructions
1. **Clone and open the project folder:**
   ```bash
   git clone [https://github.com/jhoanna-delapaz/csms-python-jhoanna-delapaz.git](https://github.com/jhoanna-delapaz/csms-python-jhoanna-delapaz.git)
   cd csms-python-jhoanna-delapaz
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```
4. **Start the application locally:**
   ```bash
   flask --app csms run --debug
   ```
   Open `http://127.0.0.1:5000/` (or `/dashboard`) in your browser, or visit `http://127.0.0.1:5000/health`.

---

## 5. Release Version Behavior (`/health` & UI)
- **Single Source of Truth:** `BaseConfig.APP_VERSION = "1.0.0"` in `src/csms/config.py` (matched with `version = "1.0.0"` in `pyproject.toml`).
- **Health Endpoint (`GET /health`):** Returns HTTP `200` with JSON:
  ```json
  {
    "application": "Community Services Management System",
    "status": "ok",
    "version": "1.0.0"
  }
  ```
  Does not show any secret keys, passwords, or file paths.
- **User Interface:** Shows `v1.0.0` using `v{{ config.APP_VERSION }}` in the top navigation bar (`src/csms/templates/navbar.html`) across Dashboard, Residents, and Service Requests.

---

## 6. Known Limitations
- **Carried Forward from T15:** No release-blocking issues found within the CSMS v1.0.0 scope.
- **Intentional Scope Limits (Feature Freeze):** User logins/roles, resident reactivation, permanent record deletion, pagination, file exports, and audit history logs are left out on purpose under the v1.0.0 rules.