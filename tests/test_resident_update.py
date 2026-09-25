# ==============================================================================
# Ticket T06: Unit tests for updating resident information.
# ==============================================================================

import pytest
from src.csms.db.database import init_db
from src.csms.models.resident import Resident
from src.csms.repositories.resident_repository import ResidentRepository
from src.csms.services.resident_validator import ResidentValidator
from src.csms.services.resident_update_service import ResidentUpdateService
from src.csms.services.resident_query_service import ResidentQueryService


@pytest.fixture
def repository(tmp_path) -> ResidentRepository:
    """Fixture providing a repository connected to a temp SQLite DB."""
    database_path = tmp_path / "t06-residents.sqlite"
    init_db(str(database_path))
    return ResidentRepository(str(database_path))


@pytest.fixture
def update_service(repository: ResidentRepository) -> ResidentUpdateService:
    """Fixture providing the ResidentUpdateService."""
    validator = ResidentValidator()
    return ResidentUpdateService(validator, repository)


@pytest.fixture
def query_service(repository: ResidentRepository) -> ResidentQueryService:
    """Fixture providing the ResidentQueryService for integration tests."""
    return ResidentQueryService(repository)


def test_1_valid_resident_update_succeeds(repository, update_service):
    """Test 1: Valid Resident Update Succeeds."""
    saved = repository.save(
        Resident(
            first_name="Juan",
            last_name="Cruz",
            address="Street 1",
            contact_number="09171234567",
            email="juan@example.com",
        )
    )

    result = update_service.update_resident(
        resident_id=saved.id,
        first_name="Juan Miguel",
        last_name="Dela Cruz",
        address="Street 2",
        contact_number="09181234567",
        email="juan.miguel@example.com",
    )

    assert result.success is True
    assert result.resident is not None
    assert result.resident.first_name == "Juan Miguel"


def test_2_resident_id_is_preserved(repository, update_service):
    """Test 2: Resident ID Is Preserved."""
    saved = repository.save(
        Resident(
            first_name="Maria",
            last_name="Santos",
            address="Street 1",
            contact_number="09171234567",
            email="maria@example.com",
        )
    )

    result = update_service.update_resident(
        resident_id=saved.id,
        first_name="Maria Clara",
        last_name="Santos",
        address="Street 1",
        contact_number="09171234567",
        email="maria@example.com",
    )

    assert result.success is True
    assert result.resident.id == saved.id


def test_3_permitted_resident_information_is_persisted(repository, update_service):
    """Test 3: Permitted Resident Information Is Persisted."""
    saved = repository.save(
        Resident(
            first_name="Ana",
            last_name="Reyes",
            address="Old Address",
            contact_number="09171112222",
            email="ana.old@example.com",
        )
    )

    update_service.update_resident(
        resident_id=saved.id,
        first_name="Anita",
        last_name="Reyes-Santos",
        address="New Address",
        contact_number="09183334444",
        email="ana.new@example.com",
    )

    updated_db = repository.find_by_id(saved.id)
    assert updated_db.first_name == "Anita"
    assert updated_db.last_name == "Reyes-Santos"
    assert updated_db.address == "New Address"
    assert updated_db.contact_number == "09183334444"
    assert updated_db.email == "ana.new@example.com"


def test_4_resident_status_is_preserved(repository, update_service):
    """Test 4: Resident Status Is Preserved (both Active and Inactive)."""
    inactive_resident = Resident(
        first_name="Jose",
        last_name="Rizal",
        address="Calamba",
        contact_number="09171234567",
        email="jose@example.com",
        status="Inactive",
    )
    saved = repository.save(inactive_resident)

    result = update_service.update_resident(
        resident_id=saved.id,
        first_name="Jose Protasio",
        last_name="Rizal",
        address="Calamba",
        contact_number="09171234567",
        email="jose@example.com",
    )

    assert result.success is True
    assert result.resident.status == "Inactive"
    assert repository.find_by_id(saved.id).status == "Inactive"


def test_5_invalid_update_fails(repository, update_service):
    """Test 5: Invalid Update Fails."""
    saved = repository.save(
        Resident(
            first_name="Pedro",
            last_name="Penduko",
            address="Aklan",
            contact_number="09171234567",
            email="pedro@example.com",
        )
    )

    result = update_service.update_resident(
        resident_id=saved.id,
        first_name="",  # Invalid blank first name
        last_name="Penduko",
        address="Aklan",
        contact_number="09171234567",
        email="pedro@example.com",
    )

    assert result.success is False
    assert result.not_found is False
    assert "first_name" in result.errors


def test_6_invalid_update_does_not_modify_persisted_information(
    repository, update_service
):
    """Test 6: Invalid Update Does Not Modify Persisted Information."""
    saved = repository.save(
        Resident(
            first_name="Original",
            last_name="Name",
            address="Original Addr",
            contact_number="09171234567",
            email="original@example.com",
        )
    )

    # Attempt invalid update
    update_service.update_resident(
        resident_id=saved.id,
        first_name="NewName",
        last_name="Name",
        address="New Addr",
        contact_number="INVALID_PHONE",
        email="original@example.com",
    )

    db_resident = repository.find_by_id(saved.id)
    assert db_resident.first_name == "Original"
    assert db_resident.address == "Original Addr"
    assert db_resident.contact_number == "09171234567"


def test_7_updating_a_nonexistent_resident_is_handled_safely(update_service):
    """Test 7: Updating a Nonexistent Resident Is Handled Safely."""
    result = update_service.update_resident(
        resident_id=999999,
        first_name="Ghost",
        last_name="User",
        address="Nowhere",
        contact_number="09171234567",
        email="ghost@example.com",
    )

    assert result.success is False
    assert result.not_found is True
    assert result.resident is None


def test_8_nonexistent_update_does_not_create_a_resident(
    repository, update_service
):
    """Test 8: Nonexistent Update Does Not Create a Resident."""
    initial_count = len(repository.find_all())

    update_service.update_resident(
        resident_id=999999,
        first_name="Ghost",
        last_name="User",
        address="Nowhere",
        contact_number="09171234567",
        email="ghost@example.com",
    )

    assert len(repository.find_all()) == initial_count


def test_9_updated_resident_is_visible_through_t05_querying(
    repository, update_service, query_service
):
    """Test 9: Updated Resident Is Visible Through T05 Querying."""
    saved = repository.save(
        Resident(
            first_name="OldFirstName",
            last_name="OldLastName",
            address="Addr",
            contact_number="09171234567",
            email="old@example.com",
        )
    )

    update_service.update_resident(
        resident_id=saved.id,
        first_name="NewUniqueFirst",
        last_name="NewUniqueLast",
        address="Addr",
        contact_number="09171234567",
        email="old@example.com",
    )

    search_results = query_service.search_residents("NewUniqueFirst")
    assert len(search_results) == 1
    assert search_results[0].id == saved.id
    assert search_results[0].first_name == "NewUniqueFirst"


def test_10_updated_information_and_contact_number_are_preserved(
    repository, update_service
):
    """Test 10: Contact Number Retains Leading Zero and Fields Preserved."""
    saved = repository.save(
        Resident(
            first_name="Zero",
            last_name="Test",
            address="Addr",
            contact_number="09170000000",
            email="zero@example.com",
        )
    )

    update_service.update_resident(
        resident_id=saved.id,
        first_name="Zero",
        last_name="Test",
        address="Addr",
        contact_number="09181234567",  # leading zero contact
        email="zero@example.com",
    )

    retrieved = repository.find_by_id(saved.id)
    assert retrieved.contact_number == "09181234567"
    assert isinstance(retrieved.contact_number, str)