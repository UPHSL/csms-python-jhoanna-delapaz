# ==============================================================================
# Ticket T15: System Hardening and Regression Tests.
# ==============================================================================

from datetime import date
import pytest
from csms import create_app
from csms.db.database import init_db
from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.dashboard_service import DashboardService
from csms.services.resident_registration_service import ResidentRegistrationService
from csms.services.resident_validator import ResidentValidator
from csms.services.service_request_submission_service import ServiceRequestSubmissionService

# Helper Functions ---


@pytest.fixture
def app_client(tmp_path):
    """Fixture providing a Flask test client with an isolated SQLite DB."""
    # Create isolated database path for test execution
    database_path = tmp_path / "t15-hardening.sqlite"
    # Initialize SQLite database schema
    init_db(str(database_path))

    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(database_path),
            "SECRET_KEY": "test-secret-key",
        }
    )

    
    with app.test_client() as client:
        yield client, str(database_path)


# 5 Required Hardening Tests ---


def test_malformed_route_identifier_handled_safely(app_client):
    # Category 1: Invalid or Malformed Input.
    """Test 1: Verify malformed route identifiers (non-integer string) are handled safely with a 404 response without crashing."""
    
    client, _ = app_client

    # Send GET request with a non-numeric resident ID string
    response_edit = client.get("/residents/not-a-number/edit")
    # Assert server handles malformed route safely with 404 Not Found
    assert response_edit.status_code == 404

    # Send GET request with a non-numeric service request ID string
    response_view = client.get("/service-requests/abc-invalid")
    # Assert server handles malformed route safely with 404 Not Found
    assert response_view.status_code == 404


def test_rejected_invalid_resident_update_leaves_persistence_unchanged(
    app_client,
):
    # Category 2: Rejected Mutation Protects Persistence.
    """Test 2: Verify that an invalid Resident update attempt (like blank last name) leaves the original persisted database record unchanged."""
    
    client, db_path = app_client
    repo = ResidentRepository(db_path)

    # Save a valid initial resident to SQLite
    saved_res = repo.save(
        Resident(
            first_name="Jane",
            last_name="Doe",
            address="123 Main St",
            contact_number="09171234567",
            email="jane.doe@example.com",
        )
    )

    # Attempt POST request with invalid blank last name
    response = client.post(
        f"/residents/{saved_res.id}/edit",
        data={
            "first_name": "Jane",
            "last_name": "",  # Invalid blank last name
            "address": "123 Main St",
            "contact_number": "09171234567",
            "email": "jane.doe@example.com",
        },
    )
    assert response.status_code == 400

    # Retrieve record directly from database to verify persistence state
    persisted_after = repo.find_by_id(saved_res.id)
    # Assert original last name in SQLite remained unchanged
    assert persisted_after.last_name == "Doe"


def test_dashboard_get_does_not_mutate_persistence(app_client):
    # Category 3: Read-Only Request Safety.
    """Test 3: Verify that repeated GET requests to read-only endpoints (Dashboard) do not modify resident or service request table counts."""
   
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    # Get resident count prior to GET requests
    res_count_before = res_repo.count_all()
    # Get service request count prior to GET requests
    sr_count_before = sr_repo.count_all()

    # Perform 5 repetitive GET requests to Dashboard
    for _ in range(5):
        response = client.get("/dashboard")
        assert response.status_code == 200

    # Get resident count after GET requests
    res_count_after = res_repo.count_all()
    # Get service request count after GET requests
    sr_count_after = sr_repo.count_all()

    # Assert total resident and total service request count in database is unchanged
    assert res_count_before == res_count_after
    assert sr_count_before == sr_count_after


def test_deactivated_resident_reflected_in_dashboard_and_blocks_submission(
    app_client,
):
    # Category 4: Cross-Feature Regression.
    """Test 4: Cross-feature test proving resident deactivation updates Dashboard status breakdown counts and prevents future service request submissions."""
    
    client, db_path = app_client
   
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)
    dash_service = DashboardService(res_repo, sr_repo)

    # Register a new active resident via registration service
    reg_service = ResidentRegistrationService(ResidentValidator(), res_repo)
    res = reg_service.register_resident(
        Resident(
            first_name="Cross",
            last_name="Feature",
            address="456 Elm St",
            contact_number="09181234567",
            email="cross.feature@example.com",
        )
    ).resident

    # Record active resident count from dashboard before deactivation
    initial_summary = dash_service.get_summary()
    active_before = getattr(initial_summary, "active_residents", getattr(initial_summary, "total_active_residents", 0))

    # Submit deactivation request via POST endpoint
    client.post(f"/residents/{res.id}/deactivate", follow_redirects=True)

    # Verify active resident count decreased by 1 on Dashboard
    updated_summary = dash_service.get_summary()
    active_after = getattr(updated_summary, "active_residents", getattr(updated_summary, "total_active_residents", 0))
    assert active_after == active_before - 1

    # Attempt to submit new service request for now-inactive resident using web route POST endpoint
    response = client.post(
        "/service-requests/new",
        data={
            "resident_id": str(res.id),
            "service_type": "Plumbing",
            "description": "Leaking pipe in sink",
            "date_requested": date.today().isoformat(),
        },
    )
    # Assert HTTP response rejected submission with Bad Request
    assert response.status_code == 400
    # Assert error message for inactive resident is present in response text
    assert b"Inactive" in response.data or b"inactive" in response.data


def test_recent_requests_boundary_strictly_respects_limit(app_client):
    # Category 5: Repeatability or Boundary Behavior.
    """Test 5: Verify recent service request query strictly enforces the 5-record boundary limit when more than 5 requests exist in SQLite."""
    _, db_path = app_client
 
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    # Save a valid resident to satisfy foreign key requirement
    res = res_repo.save(
        Resident(
            first_name="Boundary",
            last_name="User",
            address="789 Pine St",
            contact_number="09191234567",
            email="boundary@example.com",
        )
    )

    # Insert 7 service requests directly into database
    for i in range(7):
        sr_repo.save(
            ServiceRequest(
                resident_id=res.id,
                service_type=f"Service {i}",
                description=f"Boundary request {i}",
                date_requested=date.today(),
                status="Pending",
            )
        )

    # Query recent service requests with limit set to 5
    recent = sr_repo.find_recent(limit=5)
    # Assert query result strictly returns exactly 5 items
    assert len(recent) == 5