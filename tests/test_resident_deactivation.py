# ==============================================================================
# Ticket T07: Unit tests for resident deactivation
# ==============================================================================

import pytest

from src.csms.db.database import init_db
from src.csms.models.resident import Resident
from src.csms.repositories.resident_repository import ResidentRepository
from src.csms.services.resident_deactivation_service import (
    ResidentDeactivationService,
)

# Helper Functions ---


@pytest.fixture
def in_memory_repo(tmp_path) -> ResidentRepository:
    """Provides a repository connected to an isolated temporary SQLite DB file."""
    database_path = tmp_path / "t07-residents.sqlite"
    init_db(str(database_path))
    return ResidentRepository(str(database_path))


@pytest.fixture
def deactivation_service(in_memory_repo):
    """Provides a ResidentDeactivationService with temporary repo."""
    return ResidentDeactivationService(repository=in_memory_repo)


# 10 Required Tests ---


def test_active_resident_can_be_deactivated(
    in_memory_repo, deactivation_service
):
    # Test 1: Active Resident Can Be Deactivated
    # Arrange - set up the tests
    resident = Resident(
        first_name="Juan",
        last_name="Cruz",
        address="123 Main St",
        contact_number="09171234567",
        email="juan.cruz@example.com",
        status="Active",
    )
    saved = in_memory_repo.save(resident)

    # Act - test execution
    result = deactivation_service.deactivate_resident(saved.id)

    # Assert - result checking time :)
    assert result.success is True
    assert result.resident is not None


def test_resident_status_becomes_inactive_in_persistence(
    in_memory_repo, deactivation_service
):
    # Test 2: Resident Status Becomes Inactive in Persistence
    # Arrange
    resident = Resident(
        first_name="Juan",
        last_name="Cruz",
        address="123 Main St",
        contact_number="09171234567",
        email="juan.cruz@example.com",
        status="Active",
    )
    saved = in_memory_repo.save(resident)

    # Act
    deactivation_service.deactivate_resident(saved.id)

    # Assert
    fetched = in_memory_repo.find_by_id(saved.id)
    assert fetched is not None
    assert fetched.status == "Inactive"


def test_resident_id_is_preserved(in_memory_repo, deactivation_service):
    # Test 3: Resident ID Is Preserved
    # Arrange
    resident = Resident(
        first_name="Juan",
        last_name="Cruz",
        address="123 Main St",
        contact_number="09171234567",
        email="juan.cruz@example.com",
        status="Active",
    )
    saved = in_memory_repo.save(resident)
    original_id = saved.id

    # Act
    result = deactivation_service.deactivate_resident(original_id)

    # Assert
    assert result.resident.id == original_id


def test_resident_information_is_preserved(
    in_memory_repo, deactivation_service
):
    # Test 4: Resident Information Is Preserved
    # Arrange
    resident = Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
        status="Active",
    )
    saved = in_memory_repo.save(resident)

    # Act
    deactivation_service.deactivate_resident(saved.id)
    fetched = in_memory_repo.find_by_id(saved.id)

    # Assert
    assert fetched.first_name == "Juan"
    assert fetched.last_name == "Dela Cruz"
    assert fetched.address == "Barangay Santo Tomas"
    assert fetched.contact_number == "09171234567"
    assert fetched.email == "juan@example.com"
    assert fetched.status == "Inactive"


def test_deactivated_resident_remains_persisted_and_retrievable(
    in_memory_repo, deactivation_service
):
    # Test 5: Deactivated Resident Remains Persisted and Retrievable
    # Arrange
    resident = Resident(
        first_name="Maria",
        last_name="Santos",
        address="456 Maple St",
        contact_number="09181234567",
        email="maria@example.com",
        status="Active",
    )
    saved = in_memory_repo.save(resident)

    # Act
    deactivation_service.deactivate_resident(saved.id)

    # Assert
    fetched = in_memory_repo.find_by_id(saved.id)
    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.status == "Inactive"


def test_deactivated_resident_remains_available_through_t05(
    in_memory_repo, deactivation_service
):
    # Test 6: Deactivated Resident Remains Available Through T05
    # Arrange
    resident = Resident(
        first_name="Pedro",
        last_name="Penduko",
        address="789 Oak Ave",
        contact_number="09221234567",
        email="pedro@example.com",
        status="Active",
    )
    saved = in_memory_repo.save(resident)

    # Act
    deactivation_service.deactivate_resident(saved.id)

    # Assert
    search_results = in_memory_repo.search_by_name("Penduko")
    all_results = in_memory_repo.find_all()

    assert len(search_results) == 1
    assert search_results[0].status == "Inactive"
    assert any(
        r.id == saved.id and r.status == "Inactive" for r in all_results
    )


def test_already_inactive_resident_handled_safely(
    in_memory_repo, deactivation_service
):
    # Test 7: Already-Inactive Resident Is Handled Safely
    # Arrange
    resident = Resident(
        first_name="Ana",
        last_name="Reyes",
        address="101 Pine St",
        contact_number="09251234567",
        email="ana@example.com",
        status="Inactive",
    )
    saved = in_memory_repo.save(resident)

    # Act
    result = deactivation_service.deactivate_resident(saved.id)

    # Assert
    assert result.success is True
    assert result.already_inactive is True
    assert result.not_found is False
    assert result.resident.status == "Inactive"


def test_nonexistent_resident_handled_safely(deactivation_service):
    # Test 8: Nonexistent Resident Is Handled Safely
    # Act
    result = deactivation_service.deactivate_resident(999999)

    # Assert
    assert result.success is False
    assert result.not_found is True
    assert result.resident is None


def test_nonexistent_deactivation_does_not_create_or_delete_records(
    in_memory_repo, deactivation_service
):
    # Test 9: Nonexistent Deactivation Does Not Create or Delete Records
    # Arrange
    resident = Resident(
        first_name="Rosa",
        last_name="Flores",
        address="202 Cedar St",
        contact_number="09191234567",
        email="rosa@example.com",
        status="Active",
    )
    in_memory_repo.save(resident)
    count_before = len(in_memory_repo.find_all())

    # Act
    deactivation_service.deactivate_resident(888888)

    # Assert
    count_after = len(in_memory_repo.find_all())
    assert count_before == count_after == 1


def test_deactivating_one_resident_does_not_affect_another(
    in_memory_repo, deactivation_service
):
    # Test 10: Deactivating One Resident Does Not Affect Another
    # Arrange
    res1 = in_memory_repo.save(
        Resident(
            first_name="First",
            last_name="Resident",
            address="Addr 1",
            contact_number="09111111111",
            email="res1@example.com",
            status="Active",
        )
    )
    res2 = in_memory_repo.save(
        Resident(
            first_name="Second",
            last_name="Resident",
            address="Addr 2",
            contact_number="09222222222",
            email="res2@example.com",
            status="Active",
        )
    )

    # Act
    deactivation_service.deactivate_resident(res1.id)

    # Assert
    fetched_res1 = in_memory_repo.find_by_id(res1.id)
    fetched_res2 = in_memory_repo.find_by_id(res2.id)

    assert fetched_res1.status == "Inactive"
    assert fetched_res2.status == "Active"
    assert fetched_res2.first_name == "Second"