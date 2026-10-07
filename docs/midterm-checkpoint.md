# Midterm Checkpoint Documentation (T10)

## Section 1: Developer Information
- **Name:** Jhoanna Alexandra C. De La Paz
- **GitHub Username:** jhoanna-delapaz
- **Primary Technology Stack:** Python 3.14 / Flask 3.1 / pytest / SQLite
- **T10 Branch:** feature/t10-service-request-status

## Section 2: My T10 Implementation
The status feature is handled by `ServiceRequestStatusService`, which keeps status updates separate from the rest of the application. 

When changing a status, the service follows these steps:
1. Checks if the requested new status is a valid option.
2. Retrieves the persisted `ServiceRequest` from `ServiceRequestRepository` using its ID to check its current status.
3. Checks if changing from the current status to the new status is allowed.
4. If allowed, updates only the `status` column in the database.
5. If not allowed, stops immediately so the database remains unchanged.
6. Returns a `ServiceRequestStatusResult` object containing the result status and the updated request data.

## Section 3: My Transition Rules
The service strictly allows only these four status changes:
- `Pending` → `In Progress`
- `Pending` → `Cancelled`
- `In Progress` → `Completed`
- `In Progress` → `Cancelled`

Important rules and limits:
- **`Pending` to `Completed` is blocked**: A request must be worked on (`In Progress`) before it can be finished.
- **`Completed` is final**: Finished requests cannot be edited.
- **`Cancelled` is final**: Cancelled requests cannot be reopened.
- **Same-status updates are blocked**: Trying to change a status to what it already is (like `Pending` to `Pending`) is rejected because no actual change is happening.

## Section 4: Files I Changed
1. **`src/csms/repositories/service_request_repository.py`**
   - *Purpose:* Added `update_status()` to run safe SQL `UPDATE` queries on the database.
2. **`src/csms/services/service_request_status_result.py`**
   - *Purpose:* Created a response object that holds status results (`success`, `not_found`, `unsupported_status`, `invalid_transition`) and the updated record.
3. **`src/csms/services/service_request_status_service.py`**
   - *Purpose:* Added the core rules that check if a status change is allowed before saving to the database.
4. **`tests/test_service_request_status.py`**
   - *Purpose:* Created 14 unit tests (13 required + 1 extra student test) using pytest's built-in `tmp_path` fixture for clean database testing.

## Section 5: Problem I Encountered
During testing, 5 unit tests failed with a `TypeError` when calling the repository update method.

**Error Message:**
```text
    self.service_request_repository.update_status(requested_status)
E   TypeError: ServiceRequestRepository.update_status() missing 1 required positional argument: 'new_status'

src\csms\services\service_request_status_service.py:60: TypeError
```

I investigated by checking `src/csms/services/service_request_status_service.py` and realized I had called `self.service_request_repository.update_status(requested_status)` without passing `request_id` first. 

**Fixed Line:**
self.service_request_repository.update_status(request_id, requested_status)

I resolved this by updating the function call in `service_request_status_service.py` to pass both required arguments (`request_id` and `requested_status`), which fixed the error and allowed all 14 unit tests to pass cleanly.

## Section 6: My Student-Designed Test
- **Test Name:** `test_multiple_sequential_valid_transitions`
- **What the Test Verifies:** Checks that a single request can move through a full lifecycle (`Pending` → `In Progress` → `Completed`) across multiple steps without issue.
- **Why I Added This Test:** To make sure intermediate status changes save cleanly to the database and leave the record ready for the next valid change without locking up or corrupting data.

## Section 7: Tools and References Used
- **pytest Docs:** Used the built-in `tmp_path` fixture to automatically create and clean up temporary test databases.
- **AI Assistant:** Used as a coding collaborator to review code strcuture requirements, debug, and create documentation formats, since my formats are always messy.