# ==============================================================================
# Ticket T16: Final System Release and Development Checkpoint Tests.
# ==============================================================================

from datetime import date
import pytest
from csms import create_app
from csms.db.database import init_db
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.dashboard_service import DashboardService

# Helper Functions ---


@pytest.fixture
def app_client(tmp_path):
    """Fixture providing a Flask test client with an isolated SQLite DB."""
    # Create isolated database path
    database_path = tmp_path / "t16-final-release.sqlite"
 
    init_db(str(database_path))

    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(database_path),
            "SECRET_KEY": "test-secret-key",
        }
    )

    with app.test_client() as client:
        yield client, str(database_path), app


# Part G: Automated Release Version Verification ---


def test_health_endpoint_reports_final_release_version_safely(app_client):
    # Automated /health Release Identity & Safety Check.
    """Verify /health reports CSMS identity, version 1.0.0, ok status, and exposes no sensitive data."""
    client, _, app = app_client

    # Request the /health endpoint
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload is not None
    # Verify application identity, release version, and healthy status
    assert payload["application"] == "Community Services Management System"
    assert payload["version"] == app.config["APP_VERSION"]
    assert payload["version"] == "1.0.0"
    assert payload["status"] == "ok"

    # Verify /health does not leak secrets, tokens, or filesystem paths
    serialized = str(payload).lower()
    assert "secret" not in serialized
    assert "password" not in serialized
    assert "token" not in serialized
    assert "sqlite" not in serialized
    assert "database_path" not in serialized


def test_ui_views_display_consistent_release_version(app_client):
    # Automated UI Version Consistency Check.
    """confirm v1.0.0 is consistently displayed across all the pages that i have"""
    client, _, app = app_client

    expected_badge = f"v{app.config['APP_VERSION']}".encode("utf-8")
    assert expected_badge == b"v1.0.0"

    # check all primary navigation views for consistent version display
    for route in ["/", "/dashboard", "/residents", "/service-requests"]:
        response = client.get(route)
        assert response.status_code == 200
        assert expected_badge in response.data


# Part F: Student-Designed Final Examination Integration Test ---


def test_resident_service_request_lifecycle_and_dashboard_persistence(app_client):
    # Cross-Module Final Integration Test with Real SQLite Persistence.
    """
    Verify end-to-end integration across 5 modules,
    basically testing the whole system flow all together:
    1. Resident Registration & Persistence (T03/T04/T12)
    2. Service Request Submission & Active-Resident Eligibility (T09/T13)
    3. Service Request Controlled Status Workflow (T10/T13)
    4. Resident Deactivation Lifecycle (T07/T12)
    5. Dashboard Summary Aggregation (T14)
    """
    client, db_path, _ = app_client

    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)
    dash_service = DashboardService(res_repo, sr_repo)

    # 1. Confirm known empty starting state in SQLite persistence
    initial_summary = dash_service.get_summary()
    assert initial_summary.total_residents == 0
    assert initial_summary.total_service_requests == 0

    # 2. Register an active resident through the web route
    reg_response = client.post(
        "/residents/register",
        data={
            "first_name": "Elena",
            "last_name": "Navarro",
            "address": "42 Mabini Street, Barangay Uno",
            "contact_number": "09171234567",
            "email": "elena.navarro@example.com",
        },
        follow_redirects=False,
    )
    assert reg_response.status_code == 302

    # Verify resident is persisted as active in SQLite
    persisted_residents = res_repo.find_all()
    assert len(persisted_residents) == 1
    resident = persisted_residents[0]
    assert resident.status == "Active"

    # 3. Submit two service requests for the active resident
    sr1_response = client.post(
        "/service-requests/new",
        data={
            "resident_id": str(resident.id),
            "service_type": "Barangay Clearance",
            "description": "Employment clearance certificate request.",
            "date_requested": date.today().isoformat(),
        },
        follow_redirects=False,
    )
    assert sr1_response.status_code == 302

    sr2_response = client.post(
        "/service-requests/new",
        data={
            "resident_id": str(resident.id),
            "service_type": "Medical Assistance",
            "description": "Senior maintenance medicine support.",
            "date_requested": date.today().isoformat(),
        },
        follow_redirects=False,
    )
    assert sr2_response.status_code == 302

    # Verify both service requests are persisted in SQLite with initial Pending status
    persisted_requests = sr_repo.find_all()
    assert len(persisted_requests) == 2
    req_one = next(r for r in persisted_requests if r.service_type == "Barangay Clearance")
    req_two = next(r for r in persisted_requests if r.service_type == "Medical Assistance")
    assert req_one.status == "Pending"
    assert req_two.status == "Pending"

    # 4. Transition Request 1 through valid workflow: Pending -> In Progress -> Completed
    in_progress_resp = client.post(
        f"/service-requests/{req_one.id}/status",
        data={"action": "start_processing"},
        follow_redirects=False,
    )
    assert in_progress_resp.status_code == 302
    assert sr_repo.find_by_id(req_one.id).status == "In Progress"

    completed_resp = client.post(
        f"/service-requests/{req_one.id}/status",
        data={"action": "complete"},
        follow_redirects=False,
    )
    assert completed_resp.status_code == 302
    assert sr_repo.find_by_id(req_one.id).status == "Completed"

    # Verify invalid transition on terminal Completed request is rejected without erroring the system or changing the status
    invalid_transition_resp = client.post(
        f"/service-requests/{req_one.id}/status",
        data={"action": "start_processing"},
        follow_redirects=False,
    )
    assert invalid_transition_resp.status_code == 302
    assert sr_repo.find_by_id(req_one.id).status == "Completed"

    # 5. Deactivate the resident and verify the service request submission is blocked
    deactivate_resp = client.post(
        f"/residents/{resident.id}/deactivate",
        follow_redirects=False,
    )
    assert deactivate_resp.status_code == 302
    assert res_repo.find_by_id(resident.id).status == "Inactive"

    blocked_sr_resp = client.post(
        "/service-requests/new",
        data={
            "resident_id": str(resident.id),
            "service_type": "Indigency Certificate",
            "description": "Should be rejected because resident is inactive.",
            "date_requested": date.today().isoformat(),
        },
        follow_redirects=False,
    )
    assert blocked_sr_resp.status_code == 400
    assert b"Inactive Residents cannot submit new Service Requests." in blocked_sr_resp.data
    # Confirm rejected submission was not persisted
    assert len(sr_repo.find_all()) == 2

    # 6. Verify correct and final persisted counts and if it reflects in the Dashboard 
    final_summary = dash_service.get_summary()
    assert final_summary.total_residents == 1
    assert final_summary.active_residents == 0
    assert final_summary.inactive_residents == 1
    assert final_summary.total_service_requests == 2
    assert final_summary.open_service_requests == 1
    assert final_summary.pending_requests == 1
    assert final_summary.in_progress_requests == 0
    assert final_summary.completed_requests == 1
    assert final_summary.cancelled_requests == 0
    assert sr_repo.find_by_id(req_two.id).status == "Pending"