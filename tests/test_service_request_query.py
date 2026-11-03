# ==============================================================================
# Ticket T11: Unit tests for searching and viewing service requests.
# ==============================================================================

from datetime import date
import pytest
from src.csms.db.database import init_db
from src.csms.models.service_request import ServiceRequest
from src.csms.repositories.service_request_repository import ServiceRequestRepository
from src.csms.services.service_request_query_service import ServiceRequestQueryService

# Helper Functions ---

@pytest.fixture
def repository(tmp_path) -> ServiceRequestRepository:
    """Fixture providing a repository connected to a temp SQLite DB."""
    database_path = tmp_path / "t11-service-requests.sqlite"
    init_db(str(database_path))
    return ServiceRequestRepository(str(database_path))


@pytest.fixture
def query_service(repository: ServiceRequestRepository) -> ServiceRequestQueryService:
    """Fixture providing the ServiceRequestQueryService for integration tests."""
    return ServiceRequestQueryService(repository)


# 14 Required Tests ---

def test_list_all_persisted_service_requests(repository, query_service):
    # Test 1: List All Persisted Service Requests.
    repository.save(ServiceRequest(1, "Clearance", "Desc 1", date(2026, 9, 1)))
    repository.save(ServiceRequest(1, "Assistance", "Desc 2", date(2026, 9, 2)))

    results = query_service.list_service_requests()
    assert len(results) == 2


def test_empty_listing_returns_empty_collection(query_service):
    # Test 2: Empty Listing Returns an Empty Collection.
    results = query_service.list_service_requests()
    assert results == []


def test_listing_uses_required_ordering(repository, query_service):
    # Test 3: Listing Uses Required Ordering (dateRequested DESC, then id DESC).
    req1 = repository.save(ServiceRequest(1, "Type A", "Desc", date(2026, 9, 15)))
    req2 = repository.save(ServiceRequest(1, "Type B", "Desc", date(2026, 9, 18)))
    req3 = repository.save(ServiceRequest(1, "Type C", "Desc", date(2026, 9, 18)))
    req4 = repository.save(ServiceRequest(1, "Type D", "Desc", date(2026, 9, 10)))

    results = query_service.list_service_requests()
    expected_ids = [req3.id, req2.id, req1.id, req4.id]
    actual_ids = [r.id for r in results]
    assert actual_ids == expected_ids


def test_view_existing_service_request_by_id(repository, query_service):
    # Test 4: View Existing Service Request by ID.
    saved = repository.save(ServiceRequest(1, "Clearance", "Employment", date(2026, 9, 10)))
    retrieved = query_service.view_service_request(saved.id)

    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.service_type == "Clearance"


def test_viewing_unknown_id_handled_safely(query_service):
    # Test 5: Viewing an Unknown ID Is Handled Safely.
    result = query_service.view_service_request(9999)
    assert result is None


def test_partial_service_type_search_case_insensitive(repository, query_service):
    # Test 6: Partial Service-Type Search Is Case-Insensitive.
    repository.save(ServiceRequest(1, "Barangay Clearance", "Desc 1", date(2026, 9, 1)))
    repository.save(ServiceRequest(1, "Community Assistance", "Desc 2", date(2026, 9, 2)))

    results = query_service.search_service_requests(search_term="cLeAr")
    assert len(results) == 1
    assert results[0].service_type == "Barangay Clearance"


def test_partial_description_search_case_insensitive(repository, query_service):
    # Test 7: Partial Description Search Is Case-Insensitive.
    repository.save(ServiceRequest(1, "Assistance", "Requesting employment support", date(2026, 9, 1)))

    results = query_service.search_service_requests(search_term="eMpLoYmEnT")
    assert len(results) == 1
    assert results[0].description == "Requesting employment support"


def test_blank_search_returns_all_service_requests(repository, query_service):
    # Test 8: Blank Search Returns All Service Requests.
    repository.save(ServiceRequest(1, "Type 1", "Desc 1", date(2026, 9, 1)))
    repository.save(ServiceRequest(1, "Type 2", "Desc 2", date(2026, 9, 2)))

    results = query_service.search_service_requests(search_term="   ")
    assert len(results) == 2


def test_no_text_match_returns_empty_collection(repository, query_service):
    # Test 9: No Text Match Returns an Empty Collection.
    repository.save(ServiceRequest(1, "Clearance", "Desc 1", date(2026, 9, 1)))

    results = query_service.search_service_requests(search_term="NonExistentTerm")
    assert results == []


def test_status_filter_returns_only_matching_status(repository, query_service):
    # Test 10: Status Filter Returns Only Matching Status.
    req1 = repository.save(ServiceRequest(1, "Clearance", "Desc 1", date(2026, 9, 1), status="Pending"))
    req2 = repository.save(ServiceRequest(1, "Permit", "Desc 2", date(2026, 9, 2), status="Completed"))

    results = query_service.search_service_requests(status_filter="Pending")
    assert len(results) == 1
    assert results[0].id == req1.id
    assert results[0].status == "Pending"


def test_unfiltered_query_includes_all_statuses(repository, query_service):
    # Test 11: Unfiltered Query Includes All Statuses.
    repository.save(ServiceRequest(1, "T1", "D1", date(2026, 9, 1), status="Pending"))
    repository.save(ServiceRequest(1, "T2", "D2", date(2026, 9, 2), status="In Progress"))
    repository.save(ServiceRequest(1, "T3", "D3", date(2026, 9, 3), status="Completed"))
    repository.save(ServiceRequest(1, "T4", "D4", date(2026, 9, 4), status="Cancelled"))

    results = query_service.search_service_requests()
    assert len(results) == 4


def test_combined_text_search_and_status_filter(repository, query_service):
    # Test 12: Combined Text Search and Status Filter.
    req_match = repository.save(ServiceRequest(1, "Barangay Clearance", "Employment", date(2026, 9, 1), status="Pending"))
    repository.save(ServiceRequest(1, "Barangay Clearance", "Scholarship", date(2026, 9, 2), status="Completed"))
    repository.save(ServiceRequest(1, "Community Assistance", "Employment", date(2026, 9, 3), status="Pending"))

    results = query_service.search_service_requests(search_term="clearance", status_filter="Pending")
    assert len(results) == 1
    assert results[0].id == req_match.id


def test_matching_service_request_not_duplicated(repository, query_service):
    # Test 13: Matching Service Request Is Not Duplicated.
    repository.save(ServiceRequest(1, "Community Assistance", "Assistance requested", date(2026, 9, 1)))

    results = query_service.search_service_requests(search_term="Assistance")
    assert len(results) == 1


def test_query_result_preserves_complete_information(repository, query_service):
    # Test 14: Query Result Preserves Complete Service Request Information.
    saved = repository.save(ServiceRequest(10, "Permit", "Building permit request", date(2026, 9, 15), status="Pending"))

    results = query_service.search_service_requests(search_term="Permit")
    assert len(results) == 1
    item = results[0]

    assert item.id == saved.id
    assert item.resident_id == 10
    assert item.service_type == "Permit"
    assert item.description == "Building permit request"
    assert item.date_requested == date(2026, 9, 15)
    assert item.status == "Pending"