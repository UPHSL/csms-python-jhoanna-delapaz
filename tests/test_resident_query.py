# ==============================================================================
# Ticket T05: Resident Query & Listing Tests
# ==============================================================================

from src.csms.db.database import init_db
from src.csms.models.resident import Resident
from src.csms.repositories.resident_repository import (
    ResidentRepository,
)
from src.csms.services.resident_query_service import (
    ResidentQueryService,
)

# --- Ticket T05 Test Helpers ---

def make_repository(tmp_path) -> ResidentRepository:
    """Test Helper:  Builds a fresh SQLite database and returns repository."""
    database_path = tmp_path / "t05-residents.sqlite"
    init_db(str(database_path))
    return ResidentRepository(str(database_path))


def make_query_service(repository: ResidentRepository) -> ResidentQueryService:
    """Test Helper:  Builds query service instance."""
    return ResidentQueryService(repository)


def make_resident(
    first_name: str,
    last_name: str,
    contact_number: str,
    email: str,
    status: str = "Active",
) -> Resident:
    """Test Helper:  Instantiates a Resident domain object."""
    resident = Resident(
        first_name=first_name,
        last_name=last_name,
        address="Barangay Santo Tomas",
        contact_number=contact_number,
        email=email,
    )
    if status != "Active":
        resident.status = status
    return resident


def save_resident(repository: ResidentRepository, resident: Resident) -> Resident:
    """Test Helper: Persists a resident for testing."""
    return repository.save(resident)


# --- Required T05 Test Scenarios ---

# Test 1: List All Persisted Residents
def test_lists_all_persisted_residents(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    save_resident(repository, make_resident("Juan", "Cruz", "09171234561", "juan@example.com"))
    save_resident(repository, make_resident("Maria", "Santos", "09171234562", "maria@example.com"))
    save_resident(repository, make_resident("Ana", "Reyes", "09171234563", "ana@example.com"))

    residents = service.list_residents()
    assert len(residents) == 3


# Test 2: Empty Resident Listing
def test_empty_listing_returns_empty_list(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    residents = service.list_residents()
    assert residents is not None
    assert residents == []


# Test 3: Resident Listing Uses Required Ordering (lastName ASC, firstName ASC, id ASC)
def test_listing_uses_required_ordering(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    save_resident(repository, make_resident("Ana", "Santos", "09171234561", "ana.santos@example.com"))
    save_resident(repository, make_resident("Pedro", "Cruz", "09171234562", "pedro.cruz@example.com"))
    save_resident(repository, make_resident("Maria", "Andres", "09171234563", "maria.andres@example.com"))
    save_resident(repository, make_resident("Juan", "Cruz", "09171234564", "juan.cruz@example.com"))

    residents = service.list_residents()
    names = [(resident.last_name, resident.first_name) for resident in residents]

    assert names == [
        ("Andres", "Maria"),
        ("Cruz", "Juan"),
        ("Cruz", "Pedro"),
        ("Santos", "Ana"),
    ]


# Test 4: Partial First Name Search Is Case-Insensitive (and Trims Spaces)
def test_searches_partial_first_name_case_insensitively(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    save_resident(repository, make_resident("Juan", "Dela Cruz", "09171234561", "juan@example.com"))
    save_resident(repository, make_resident("Maria", "Santos", "09171234562", "maria@example.com"))

    results = service.search_residents("   jUa   ")
    assert len(results) == 1
    assert results[0].first_name == "Juan"


# Test 5: Partial Last Name Search Is Case-Insensitive
def test_searches_partial_last_name_case_insensitively(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    save_resident(repository, make_resident("Juan", "Dela Cruz", "09171234561", "juan@example.com"))
    save_resident(repository, make_resident("Maria", "Santos", "09171234562", "maria@example.com"))

    results = service.search_residents("cRuZ")
    assert len(results) == 1
    assert results[0].last_name == "Dela Cruz"


# Test 6: Blank Search Returns All Residents
def test_blank_search_returns_all_residents(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    save_resident(repository, make_resident("Juan", "Cruz", "09171234561", "juan@example.com"))
    save_resident(repository, make_resident("Maria", "Santos", "09171234562", "maria@example.com"))

    listed = service.list_residents()
    searched = service.search_residents("      ")

    assert len(searched) == len(listed)
    assert [resident.id for resident in searched] == [resident.id for resident in listed]


# Test 7: Search With No Match Returns Empty Collection
def test_search_with_no_match_returns_empty_list(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    save_resident(repository, make_resident("Juan", "Cruz", "09171234561", "juan@example.com"))

    results = service.search_residents("ZzzUnknownResident")
    assert results is not None
    assert results == []


# Test 8: Search Result Preserves Resident Information
def test_search_result_preserves_resident_information(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    saved = save_resident(repository, make_resident("Juan", "Dela Cruz", "09171234567", "juan@example.com"))

    results = service.search_residents("Juan")
    assert len(results) == 1

    resident = results[0]
    assert resident.id == saved.id
    assert resident.first_name == "Juan"
    assert resident.last_name == "Dela Cruz"
    assert resident.address == "Barangay Santo Tomas"
    assert resident.contact_number == "09171234567"
    assert resident.email == "juan@example.com"
    assert resident.status == "Active"


# Test 9: Active and Inactive Residents Are Included
def test_listing_includes_active_and_inactive_residents(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    save_resident(repository, make_resident("Juan", "Cruz", "09171234561", "juan@example.com"))
    save_resident(repository, make_resident("Maria", "Santos", "09171234562", "maria@example.com", status="Inactive"))

    residents = service.list_residents()
    statuses = {resident.status for resident in residents}

    assert "Active" in statuses
    assert "Inactive" in statuses


# Test 10: Matching Resident Is Not Duplicated
def test_matching_resident_appears_only_once(tmp_path):
    repository = make_repository(tmp_path)
    service = make_query_service(repository)

    saved = save_resident(repository, make_resident("Ana", "Anaya", "09171234561", "ana@example.com"))

    results = service.search_residents("ana")
    assert len(results) == 1
    assert results[0].id == saved.id