# ==============================================================================
# Ticket T10: Unit tests for service request status updates
# covers required tests 1 to 13 plus 1 student-designed test
# ==============================================================================

import pytest
from datetime import date
from src.csms.models.service_request import ServiceRequest
from src.csms.repositories.service_request_repository import ServiceRequestRepository
from src.csms.services.service_request_status_service import ServiceRequestStatusService


# Helper Functions ---

"""fixture: Builds a fresh SQLite database and returns repository."""
@pytest.fixture
def repository(tmp_path):
    database_path = tmp_path / "t10-service-requests.sqlite"
    return ServiceRequestRepository(db_path=str(database_path))


"""fixture: Instantiates the status service connected to the isolated repository."""
@pytest.fixture
def service(repository):
    return ServiceRequestStatusService(service_request_repository=repository)

"""helper function: shortcut to persist sample requests."""
def helper_create_request(repository, status="Pending", resident_id=1):
    req = ServiceRequest(
        resident_id=resident_id,
        service_type="Barangay Clearance",
        description="Employment requirement",
        date_requested=date(2026, 9, 15),
        status=status,
    )
    return repository.save(req)

# 13 + 1 Required Tests ---

# Test 1: Pending Can Move to In Progress
def test_pending_can_move_to_in_progress(repository, service):
    req = helper_create_request(repository, status="Pending")
    result = service.update_status(req.id, "In Progress")

    assert result.success is True
    assert result.service_request.status == "In Progress"
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "In Progress"


# Test 2: Pending Can Move to Cancelled
def test_pending_can_move_to_cancelled(repository, service):
    req = helper_create_request(repository, status="Pending")
    result = service.update_status(req.id, "Cancelled")

    assert result.success is True
    assert result.service_request.status == "Cancelled"
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "Cancelled"


# Test 3: In Progress Can Move to Completed
def test_in_progress_can_move_to_completed(repository, service):
    req = helper_create_request(repository, status="Pending")
    service.update_status(req.id, "In Progress")

    result = service.update_status(req.id, "Completed")
    assert result.success is True
    assert result.service_request.status == "Completed"
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "Completed"


# Test 4: In Progress Can Move to Cancelled
def test_in_progress_can_move_to_cancelled(repository, service):
    req = helper_create_request(repository, status="Pending")
    service.update_status(req.id, "In Progress")

    result = service.update_status(req.id, "Cancelled")
    assert result.success is True
    assert result.service_request.status == "Cancelled"
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "Cancelled"


# Test 5: Pending Cannot Move Directly to Completed
def test_pending_cannot_move_directly_to_completed(repository, service):
    req = helper_create_request(repository, status="Pending")
    result = service.update_status(req.id, "Completed")

    assert result.success is False
    assert result.invalid_transition is True
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "Pending"


# Test 6: In Progress Cannot Return to Pending
def test_in_progress_cannot_return_to_pending(repository, service):
    req = helper_create_request(repository, status="Pending")
    service.update_status(req.id, "In Progress")

    result = service.update_status(req.id, "Pending")
    assert result.success is False
    assert result.invalid_transition is True
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "In Progress"


# Test 7: Completed Is Terminal
def test_completed_is_terminal(repository, service):
    req = helper_create_request(repository, status="Pending")
    service.update_status(req.id, "In Progress")
    service.update_status(req.id, "Completed")

    result = service.update_status(req.id, "In Progress")
    assert result.success is False
    assert result.invalid_transition is True
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "Completed"


# Test 8: Cancelled Is Terminal
def test_cancelled_is_terminal(repository, service):
    req = helper_create_request(repository, status="Pending")
    service.update_status(req.id, "Cancelled")

    result = service.update_status(req.id, "In Progress")
    assert result.success is False
    assert result.invalid_transition is True
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "Cancelled"


# Test 9: Unsupported Status Is Rejected
def test_unsupported_status_is_rejected(repository, service):
    req = helper_create_request(repository, status="Pending")
    result = service.update_status(req.id, "Approved")

    assert result.success is False
    assert result.unsupported_status is True
    persisted = repository.find_by_id(req.id)
    assert persisted.status == "Pending"


# Test 10: Nonexistent Service Request Is Handled Safely
def test_nonexistent_service_request_is_handled_safely(repository, service):
    result = service.update_status(999, "In Progress")

    assert result.success is False
    assert result.not_found is True
    assert repository.find_by_id(999) is None


# Test 11: Successful Transition Preserves Service Request Information
def test_successful_transition_preserves_service_request_information(
    repository, service
):
    req = helper_create_request(repository, status="Pending")
    original_id = req.id
    original_resident_id = req.resident_id
    original_type = req.service_type
    original_desc = req.description
    original_date = req.date_requested

    result = service.update_status(req.id, "In Progress")
    assert result.success is True

    updated = result.service_request
    assert updated.id == original_id
    assert updated.resident_id == original_resident_id
    assert updated.service_type == original_type
    assert updated.description == original_desc
    assert updated.date_requested == original_date
    assert updated.status == "In Progress"


# Test 12: Invalid Transition Does Not Modify Persistence
def test_invalid_transition_does_not_modify_persistence(repository, service):
    req = helper_create_request(repository, status="Pending")

    result = service.update_status(req.id, "Completed")
    assert result.success is False

    refetched = repository.find_by_id(req.id)
    assert refetched.status == "Pending"
    assert refetched.service_type == "Barangay Clearance"


# Test 13: Same-Status Request Is Rejected
def test_same_status_request_is_rejected(repository, service):
    req = helper_create_request(repository, status="Pending")

    result = service.update_status(req.id, "Pending")
    assert result.success is False
    assert result.invalid_transition is True
    assert repository.find_by_id(req.id).status == "Pending"


# Student-Designed Test: A Single Request Going Through Multiple Sequential Valid Transitions 
# (inspired from a previously designed test)

def test_multiple_sequential_valid_transitions(repository, service):
    req = helper_create_request(repository, status="Pending")

    step1 = service.update_status(req.id, "In Progress")
    assert step1.success is True
    assert repository.find_by_id(req.id).status == "In Progress"

    step2 = service.update_status(req.id, "Completed")
    assert step2.success is True
    assert repository.find_by_id(req.id).status == "Completed"