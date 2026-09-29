# ==============================================================================
# Ticket T09: Tests for Service Request Submission 
# ==============================================================================

import pytest
from datetime import date
from src.csms.db.database import init_db
from src.csms.models.resident import Resident
from src.csms.models.service_request import ServiceRequest
from src.csms.repositories.resident_repository import ResidentRepository
from src.csms.repositories.service_request_repository import ServiceRequestRepository
from src.csms.services.service_request_validator import ServiceRequestValidator
from src.csms.services.service_request_submission_service import (
    ServiceRequestSubmissionService,
)

# --- Helper Fixtures ---

@pytest.fixture
def db_path(tmp_path):
    """Fixture providing a temporary SQLite database path."""
    path = tmp_path / "t09-csms.sqlite"
    init_db(str(path))
    return str(path)


@pytest.fixture
def resident_repo(db_path) -> ResidentRepository:
    """Fixture providing a ResidentRepository connected to temp DB."""
    return ResidentRepository(db_path)


@pytest.fixture
def service_request_repo(db_path) -> ServiceRequestRepository:
    """Fixture providing a ServiceRequestRepository connected to temp DB."""
    return ServiceRequestRepository(db_path)


@pytest.fixture
def submission_service(
    resident_repo, service_request_repo
) -> ServiceRequestSubmissionService:
    """Fixture providing the ServiceRequestSubmissionService."""
    validator = ServiceRequestValidator()
    return ServiceRequestSubmissionService(
        validator=validator,
        resident_repository=resident_repo,
        service_request_repository=service_request_repo,
    )


@pytest.fixture
def active_resident(resident_repo) -> Resident:
    """Fixture saving and returning an Active Resident."""
    return resident_repo.save(
        Resident(
            first_name="Juan",
            last_name="Dela Cruz",
            address="123 Barangay St",
            contact_number="09171234567",
            email="juan@example.com",
            status="Active",
        )
    )


# --- 13 Required Test Scenarios + Date Validation ---


def test_valid_service_request_submission_succeeds(
    active_resident, submission_service
):
    # Test 1: Valid Service Request Submission Succeeds.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Barangay Clearance",
        description="Requesting clearance for employment.",
        date_requested=date(2026, 9, 15),
    )

    result = submission_service.submit(request)

    assert result.success is True
    assert result.service_request is not None
    assert result.resident_not_found is False
    assert result.resident_inactive is False


def test_submitted_service_request_receives_generated_id(
    active_resident, submission_service
):
    # Test 2: Submitted Service Request Receives a Generated ID.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Certificate Request",
        description="Indigency certificate request.",
        date_requested=date(2026, 9, 16),
    )

    assert request.id is None  # pre-condition: unassigned ID

    result = submission_service.submit(request)

    assert result.success is True
    assert result.service_request.id is not None
    assert isinstance(result.service_request.id, int)
    assert result.service_request.id > 0


def test_submitted_service_request_is_persisted_and_retrievable(
    active_resident, submission_service, service_request_repo
):
    # Test 3: Submitted Service Request Is Persisted and Retrievable.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Community Assistance",
        description="Assistance for calamity relief.",
        date_requested=date(2026, 9, 17),
    )

    result = submission_service.submit(request)
    generated_id = result.service_request.id

    retrieved = service_request_repo.find_by_id(generated_id)
    assert retrieved is not None
    assert retrieved.id == generated_id


def test_submitted_service_request_information_is_preserved(
    active_resident, submission_service, service_request_repo
):
    # Test 4: Submitted Service Request Information Is Preserved.
    req_date = date(2026, 9, 18)
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Permit Request",
        description="Barangay business permit request.",
        date_requested=req_date,
    )

    result = submission_service.submit(request)
    retrieved = service_request_repo.find_by_id(result.service_request.id)

    assert retrieved.resident_id == active_resident.id
    assert retrieved.service_type == "Permit Request"
    assert retrieved.description == "Barangay business permit request."
    assert retrieved.date_requested == req_date
    assert retrieved.status == "Pending"


def test_submitted_service_request_status_is_pending(
    active_resident, submission_service, service_request_repo
):
    # Test 5: Submitted Service Request Status Is Pending.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Barangay Clearance",
        description="General clearance request.",
        date_requested=date(2026, 9, 19),
    )

    result = submission_service.submit(request)
    assert result.service_request.status == "Pending"

    retrieved = service_request_repo.find_by_id(result.service_request.id)
    assert retrieved.status == "Pending"


def test_blank_service_type_fails_validation(active_resident, submission_service):
    # Test 6: Blank Service Type Fails Validation.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="   ",  # Whitespace-only
        description="Valid description text.",
        date_requested=date(2026, 9, 20),
    )

    result = submission_service.submit(request)

    assert result.success is False
    assert "service_type" in result.errors


def test_blank_description_fails_validation(active_resident, submission_service):
    # Test 7: Blank Description Fails Validation.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Barangay Clearance",
        description="",  # Blank description
        date_requested=date(2026, 9, 21),
    )

    result = submission_service.submit(request)

    assert result.success is False
    assert "description" in result.errors


def test_invalid_request_does_not_reach_persistence(
    active_resident, submission_service, service_request_repo, db_path
):
    # Test 8: Invalid Request Does Not Reach Persistence.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="",  # Invalid blank service type
        description="",  # Invalid blank description
        date_requested=date(2026, 9, 22),
    )

    result = submission_service.submit(request)
    assert result.success is False

    # check no row was created in database
    conn = service_request_repo._get_connection()
    count = conn.cursor().execute("SELECT COUNT(*) FROM service_requests").fetchone()[0]
    conn.close()
    assert count == 0


def test_nonexistent_resident_prevents_submission(
    submission_service, service_request_repo
):
    # Test 9: Nonexistent Resident Prevents Submission.
    request = ServiceRequest(
        resident_id=999999,  # valid ID that does not exist in DB
        service_type="Barangay Clearance",
        description="Request for non-existent resident.",
        date_requested=date(2026, 9, 23),
    )

    result = submission_service.submit(request)

    assert result.success is False
    assert result.resident_not_found is True

    # confirm not persisted
    conn = service_request_repo._get_connection()
    count = conn.cursor().execute("SELECT COUNT(*) FROM service_requests").fetchone()[0]
    conn.close()
    assert count == 0


def test_inactive_resident_cannot_submit_a_new_service_request(
    resident_repo, submission_service, service_request_repo
):
    # Test 10: Inactive Resident Cannot Submit a New Service Request.
    inactive_resident = resident_repo.save(
        Resident(
            first_name="Maria",
            last_name="Clara",
            address="456 Heritage St",
            contact_number="09181234567",
            email="maria@example.com",
            status="Inactive",
        )
    )

    request = ServiceRequest(
        resident_id=inactive_resident.id,
        service_type="Barangay Clearance",
        description="Request attempt by inactive resident.",
        date_requested=date(2026, 9, 24),
    )

    result = submission_service.submit(request)

    assert result.success is False
    assert result.resident_inactive is True

    # check resident remains inactive 
    refetched_resident = resident_repo.find_by_id(inactive_resident.id)
    assert refetched_resident.status == "Inactive"

    # confirm not persisted
    conn = service_request_repo._get_connection()
    count = conn.cursor().execute("SELECT COUNT(*) FROM service_requests").fetchone()[0]
    conn.close()
    assert count == 0


def test_non_pending_initial_status_is_rejected(
    active_resident, submission_service
):
    # Test 11: Non-Pending Initial Status Is Rejected.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Barangay Clearance",
        description="Attempting an invalid status submission.",
        date_requested=date(2026, 9, 25),
        status="Completed",  # invalid non-Pending initial status
    )

    result = submission_service.submit(request)

    assert result.success is False
    assert "status" in result.errors


def test_service_request_persists_across_repository_access(
    active_resident, submission_service, db_path
):
    # Test 12: Service Request Persists Across Repository Access.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Certificate Request",
        description="Cross-repository test.",
        date_requested=date(2026, 9, 26),
    )

    result = submission_service.submit(request)
    generated_id = result.service_request.id

    # a completely separate repository instance reading the same DB file
    separate_repo = ServiceRequestRepository(db_path)
    retrieved = separate_repo.find_by_id(generated_id)

    assert retrieved is not None
    assert retrieved.id == generated_id
    assert retrieved.service_type == "Certificate Request"


def test_submission_does_not_modify_the_resident(
    active_resident, submission_service, resident_repo
):
    # Test 13: Submission Does Not Modify the Resident.
    request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Barangay Clearance",
        description="Resident details remain unchanged.",
        date_requested=date(2026, 9, 27),
    )

    submission_service.submit(request)

    refetched_resident = resident_repo.find_by_id(active_resident.id)
    assert refetched_resident.id == active_resident.id
    assert refetched_resident.first_name == "Juan"
    assert refetched_resident.last_name == "Dela Cruz"
    assert refetched_resident.address == "123 Barangay St"
    assert refetched_resident.contact_number == "09171234567"
    assert refetched_resident.email == "juan@example.com"
    assert refetched_resident.status == "Active"


def test_date_validation_absent_or_invalid_date_fails(
    active_resident, submission_service
):
    # Date Validation Test: Invalid or absent date requested cannot be submitted.
    invalid_request = ServiceRequest(
        resident_id=active_resident.id,
        service_type="Barangay Clearance",
        description="Request with invalid date.",
        date_requested="2026-13-45",  # invalid non-date example
    )

    result = submission_service.submit(invalid_request)

    assert result.success is False
    assert "date_requested" in result.errors