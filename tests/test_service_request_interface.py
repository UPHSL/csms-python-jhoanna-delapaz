# ==============================================================================
# Ticket T13: Presentation and integration tests for Service Request UI.
# ==============================================================================

import datetime
import pytest
from csms import create_app
from csms.db.database import init_db
from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository

# Helper Functions ---


@pytest.fixture
def app_client(tmp_path):
    """Fixture providing a Flask test client with an isolated SQLite DB."""
    database_path = tmp_path / "t13-service-requests.sqlite"
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


def _create_resident(db_path, first_name="Juan", last_name="Cruz", status="Active"):
    """Helper function to create and persist a resident for testing eligibility."""
    repo = ResidentRepository(db_path)
    return repo.save(
        Resident(
            first_name=first_name,
            last_name=last_name,
            address="Sample Street",
            contact_number="09171234567",
            email="juan.cruz@example.com",
            status=status,
        )
    ).id


# 20 Required Tests ---


def test_service_request_management_page_loads_successfully(app_client):
    # Test 1: Service Request Management Page Loads Successfully.
    client, _ = app_client
    response = client.get("/service-requests")
    assert response.status_code == 200
    assert b"Service Request Management" in response.data


def test_persisted_service_requests_are_displayed(app_client):
    # Test 2: Persisted Service Requests Are Displayed.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Barangay Clearance",
            description="Clearance for employment.",
            date_requested=datetime.date(2026, 10, 15),
            status="Pending",
        )
    )

    response = client.get("/service-requests")
    assert response.status_code == 200
    assert b"Barangay Clearance" in response.data


def test_required_ordering_is_preserved(app_client):
    # Test 3: Required Ordering Is Preserved (dateRequested DESC, then id DESC).
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Type Older Date",
            description="Older",
            date_requested=datetime.date(2026, 10, 1),
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Type Newer Date",
            description="Newer",
            date_requested=datetime.date(2026, 10, 15),
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Type Same Date Higher ID",
            description="Same Date",
            date_requested=datetime.date(2026, 10, 15),
        )
    )

    response = client.get("/service-requests")
    html = response.data.decode("utf-8")

    pos_sr3 = html.find("Type Same Date Higher ID")
    pos_sr2 = html.find("Type Newer Date")
    pos_sr1 = html.find("Type Older Date")

    assert pos_sr3 != -1 and pos_sr2 != -1 and pos_sr1 != -1
    assert pos_sr3 < pos_sr2 < pos_sr1


def test_text_search_uses_existing_query_behavior(app_client):
    # Test 4: Text Search Uses T11 Query Behavior.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Barangay Clearance",
            description="Employment requirement",
            date_requested=datetime.date(2026, 10, 10),
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Business Permit",
            description="Store renewal",
            date_requested=datetime.date(2026, 10, 10),
        )
    )

    response = client.get("/service-requests?search=CLEARANCE")
    assert response.status_code == 200
    assert b"Barangay Clearance" in response.data
    assert b"Business Permit" not in response.data


def test_status_filter_uses_existing_query_behavior(app_client):
    # Test 5: Status Filter Uses T11 Query Behavior.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Item Pending",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Pending",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Item Completed",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Completed",
        )
    )

    response = client.get("/service-requests?status=Completed")
    assert response.status_code == 200
    assert b"Item Completed" in response.data
    assert b"Item Pending" not in response.data


def test_combined_search_and_status_filter_works(app_client):
    # Test 6: Combined Search and Status Filter Works.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Clearance - Match Both",
            description="Match Both",
            date_requested=datetime.date(2026, 10, 10),
            status="Pending",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Clearance - Match Text Only",
            description="Match Text Only",
            date_requested=datetime.date(2026, 10, 10),
            status="Completed",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Permit - Match Status Only",
            description="Match Status Only",
            date_requested=datetime.date(2026, 10, 10),
            status="Pending",
        )
    )

    response = client.get("/service-requests?search=clearance&status=Pending")
    assert response.status_code == 200
    assert b"Clearance - Match Both" in response.data
    assert b"Clearance - Match Text Only" not in response.data
    assert b"Permit - Match Status Only" not in response.data


def test_submission_form_is_accessible(app_client):
    # Test 7: Submission Form Is Accessible.
    client, _ = app_client
    response = client.get("/service-requests/new")
    assert response.status_code == 200
    assert b'name="resident_id"' in response.data
    assert b'name="service_type"' in response.data
    assert b'name="description"' in response.data
    assert b'name="date_requested"' in response.data


def test_valid_submission_persists_a_pending_request(app_client):
    # Test 8: Valid Submission Persists a Pending Request.
    client, db_path = app_client
    res_id = _create_resident(db_path)

    response = client.post(
        "/service-requests/new",
        data={
            "resident_id": str(res_id),
            "service_type": "Street Repair",
            "description": "Fix pothole in front of house.",
            "date_requested": "2026-10-10",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Service Request submitted successfully." in response.data

    sr_repo = ServiceRequestRepository(db_path)
    requests = sr_repo.find_all()
    assert len(requests) == 1
    assert requests[0].resident_id == res_id
    assert requests[0].service_type == "Street Repair"
    assert requests[0].status == "Pending"


def test_invalid_submission_shows_validation_feedback_and_does_not_persist(
    app_client,
):
    # Test 9: Invalid Submission Shows Validation Feedback and Does Not Persist.
    client, db_path = app_client
    res_id = _create_resident(db_path)

    response = client.post(
        "/service-requests/new",
        data={
            "resident_id": str(res_id),
            "service_type": "   ",  # Blank service type
            "description": "Valid description",
            "date_requested": "2026-10-10",
        },
    )
    assert response.status_code == 400
    assert b"Service type is required." in response.data or b"error" in response.data.lower()

    sr_repo = ServiceRequestRepository(db_path)
    assert len(sr_repo.find_all()) == 0


def test_missing_resident_submission_is_rejected(app_client):
    # Test 10: Missing Resident Submission Is Rejected.
    client, db_path = app_client

    response = client.post(
        "/service-requests/new",
        data={
            "resident_id": "9999",
            "service_type": "Barangay Clearance",
            "description": "Test request",
            "date_requested": "2026-10-10",
        },
    )
    assert response.status_code == 400
    assert b"Resident not found." in response.data

    sr_repo = ServiceRequestRepository(db_path)
    assert len(sr_repo.find_all()) == 0


def test_inactive_resident_submission_is_rejected(app_client):
    # Test 11: Inactive Resident Submission Is Rejected.
    client, db_path = app_client
    res_id = _create_resident(db_path, status="Inactive")

    response = client.post(
        "/service-requests/new",
        data={
            "resident_id": str(res_id),
            "service_type": "Barangay Clearance",
            "description": "Test request",
            "date_requested": "2026-10-10",
        },
    )
    assert response.status_code == 400
    assert b"Inactive Residents cannot submit new Service Requests." in response.data

    sr_repo = ServiceRequestRepository(db_path)
    assert len(sr_repo.find_all()) == 0


def test_existing_service_request_details_can_be_viewed(app_client):
    # Test 12: Existing Service Request Details Can Be Viewed.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    saved_sr = sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Medical Assistance",
            description="Request for financial medical aid.",
            date_requested=datetime.date(2026, 10, 5),
            status="Pending",
        )
    )

    response = client.get(f"/service-requests/{saved_sr.id}")
    assert response.status_code == 200
    assert b"Medical Assistance" in response.data
    assert b"Request for financial medical aid." in response.data


def test_missing_service_request_view_is_handled_safely(app_client):
    # Test 13: Missing Service Request View Is Handled Safely.
    client, _ = app_client
    response = client.get("/service-requests/99999")
    assert response.status_code == 404


def test_pending_request_can_start_processing(app_client):
    # Test 14: Pending Request Can Start Processing.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    saved_sr = sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Clearance",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Pending",
        )
    )

    response = client.post(
        f"/service-requests/{saved_sr.id}/status",
        data={"action": "start_processing"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Service Request is now In Progress." in response.data

    updated_sr = sr_repo.find_by_id(saved_sr.id)
    assert updated_sr.status == "In Progress"


def test_pending_request_can_be_cancelled(app_client):
    # Test 15: Pending Request Can Be Cancelled.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    saved_sr = sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Clearance",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Pending",
        )
    )

    response = client.post(
        f"/service-requests/{saved_sr.id}/status",
        data={"action": "cancel"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Service Request cancelled successfully." in response.data

    updated_sr = sr_repo.find_by_id(saved_sr.id)
    assert updated_sr.status == "Cancelled"


def test_in_progress_request_can_be_completed(app_client):
    # Test 16: In-Progress Request Can Be Completed.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    saved_sr = sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Clearance",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="In Progress",
        )
    )

    response = client.post(
        f"/service-requests/{saved_sr.id}/status",
        data={"action": "complete"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Service Request completed successfully." in response.data

    updated_sr = sr_repo.find_by_id(saved_sr.id)
    assert updated_sr.status == "Completed"


def test_in_progress_request_can_be_cancelled(app_client):
    # Test 17: In-Progress Request Can Be Cancelled.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    saved_sr = sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Clearance",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="In Progress",
        )
    )

    response = client.post(
        f"/service-requests/{saved_sr.id}/status",
        data={"action": "cancel"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Service Request cancelled successfully." in response.data

    updated_sr = sr_repo.find_by_id(saved_sr.id)
    assert updated_sr.status == "Cancelled"


def test_invalid_direct_transition_is_still_rejected(app_client):
    # Test 18: Invalid Direct Transition Is Still Rejected.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    saved_sr = sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Clearance",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Pending",
        )
    )

    # Attempt illegal direct transition from Pending to Completed
    response = client.post(
        f"/service-requests/{saved_sr.id}/status",
        data={"action": "complete"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    updated_sr = sr_repo.find_by_id(saved_sr.id)
    assert updated_sr.status == "Pending"  # Status remains unchanged


def test_completed_and_cancelled_requests_remain_visible(app_client):
    # Test 19: Completed and Cancelled Requests Remain Visible.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Terminal Completed",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Completed",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="Terminal Cancelled",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Cancelled",
        )
    )

    response = client.get("/service-requests")
    assert response.status_code == 200
    assert b"Terminal Completed" in response.data
    assert b"Terminal Cancelled" in response.data


def test_get_requests_do_not_change_service_request_state(app_client):
    # Test 20: GET Requests Do Not Change Service Request State.
    client, db_path = app_client
    res_id = _create_resident(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    saved_sr = sr_repo.save(
        ServiceRequest(
            resident_id=res_id,
            service_type="ReadOnly Check",
            description="Desc",
            date_requested=datetime.date(2026, 10, 10),
            status="Pending",
        )
    )

    # Perform GET operations
    client.get("/service-requests")
    client.get(f"/service-requests/{saved_sr.id}")
    client.get("/service-requests/new")
    client.get("/service-requests?search=ReadOnly")

    updated_sr = sr_repo.find_by_id(saved_sr.id)
    assert updated_sr.status == "Pending"
    assert len(sr_repo.find_all()) == 1