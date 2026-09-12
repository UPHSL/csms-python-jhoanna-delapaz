# T04 TESTS

import sqlite3

from src.csms.db.database import init_db
from src.csms.models.resident import Resident
from src.csms.repositories.resident_repository import (
    ResidentRepository,
)
from src.csms.services.resident_registration_result import (
    ResidentRegistrationResult,
)
from src.csms.services.resident_registration_service import (
    ResidentRegistrationService,
)
from src.csms.services.resident_validator import (
    ResidentValidator,
)


# Steps 27–31: Helper Functions ---

def make_repository(tmp_path) -> ResidentRepository:
    """Helper to create isolated repository for each test."""
    database_path = tmp_path / "residents.sqlite"
    init_db(str(database_path))
    return ResidentRepository(str(database_path))


def make_registration_service(repository: ResidentRepository) -> ResidentRegistrationService:
    """Helper to create service with validator and repository dependencies."""
    validator = ResidentValidator()
    return ResidentRegistrationService(validator, repository)


def make_valid_resident() -> Resident:
    """Helper returning valid resident with default Active status."""
    return Resident(
        first_name="Juan",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
    )


def make_resident_with_missing_first_name() -> Resident:
    """Helper returning invalid resident violating T02 validation rules."""
    return Resident(
        first_name="",
        last_name="Dela Cruz",
        address="Barangay Santo Tomas",
        contact_number="09171234567",
        email="juan@example.com",
    )


def count_residents(database_path: str) -> int:
    """Direct SQLite query helper to verify row counts in tests."""
    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute("SELECT COUNT(*) FROM residents")
        row = cursor.fetchone()
        return int(row[0])


# Steps 32–42: Eight Required Tests ---

def test_registers_valid_resident(tmp_path):
    # Test 1: Register a Valid Resident
    repository = make_repository(tmp_path)
    service = make_registration_service(repository)
    resident = make_valid_resident()

    result = service.register_resident(resident)

    assert result.success is True
    assert result.resident is not None
    assert result.errors == []


def test_registered_resident_receives_identifier(tmp_path):
    # Test 2: Registered Resident Receives an Identifier
    repository = make_repository(tmp_path)
    service = make_registration_service(repository)
    resident = make_valid_resident()

    assert resident.id is None

    result = service.register_resident(resident)

    assert result.success is True
    assert result.resident is not None
    assert result.resident.id is not None


def test_registered_resident_is_persisted(tmp_path):
    # Test 3: Registered Resident Is Actually Persisted
    repository = make_repository(tmp_path)
    service = make_registration_service(repository)
    resident = make_valid_resident()

    result = service.register_resident(resident)

    assert result.success is True
    assert result.resident is not None
    assert result.resident.id is not None

    stored_resident = repository.find_by_id(result.resident.id)

    assert stored_resident is not None
    assert stored_resident.id == result.resident.id


def test_registered_resident_information_is_preserved(tmp_path):
    # Test 4: Resident Information Is Preserved
    repository = make_repository(tmp_path)
    service = make_registration_service(repository)
    resident = make_valid_resident()

    result = service.register_resident(resident)

    stored_resident = repository.find_by_id(result.resident.id)

    assert stored_resident is not None
    assert stored_resident.first_name == "Juan"
    assert stored_resident.last_name == "Dela Cruz"
    assert stored_resident.address == "Barangay Santo Tomas"
    assert stored_resident.contact_number == "09171234567"
    assert stored_resident.email == "juan@example.com"
    assert stored_resident.status == "Active"


def test_registration_preserves_default_active_status(tmp_path):
    # Test 5: Preserve the Default Active Status
    repository = make_repository(tmp_path)
    service = make_registration_service(repository)
    resident = make_valid_resident()

    assert resident.status == "Active"

    result = service.register_resident(resident)

    assert result.success is True
    assert result.resident is not None
    assert result.resident.status == "Active"


def test_invalid_resident_registration_fails(tmp_path):
    # Test 6: Invalid Registration Must Fail
    repository = make_repository(tmp_path)
    service = make_registration_service(repository)
    resident = make_resident_with_missing_first_name()

    result = service.register_resident(resident)

    assert result.success is False
    assert result.resident is None
    assert result.errors


def test_invalid_resident_is_not_persisted(tmp_path):
    # Test 7: Invalid Resident Is Not Persisted
    database_path = tmp_path / "residents.sqlite"
    init_db(str(database_path))

    repository = ResidentRepository(str(database_path))
    service = make_registration_service(repository)
    resident = make_resident_with_missing_first_name()

    count_before = count_residents(str(database_path))
    result = service.register_resident(resident)
    count_after = count_residents(str(database_path))

    assert result.success is False
    assert count_after == count_before


def test_registration_identifies_validation_failure(tmp_path):
    # Test 8: Validation Failure Can Be Identified
    repository = make_repository(tmp_path)
    service = make_registration_service(repository)
    resident = make_resident_with_missing_first_name()

    result = service.register_resident(resident)

    assert result.success is False
    assert "first_name" in result.errors