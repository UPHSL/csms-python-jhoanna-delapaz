import pytest
from src.csms.db.database import init_db
from src.csms.models.resident import Resident
from src.csms.repositories.resident_repository import ResidentRepository


@pytest.fixture
def repo(tmp_path):
    """Pytest fixture is known to set up an isolated SQLite test database for each test."""
    # Create a temporary database file path unique to this test
    db_file = tmp_path / "test_csms.db"
    db_path = str(db_file)
    # Build the database tables inside the temporary file
    init_db(db_path)
    # Return a repository connected to this temporary test database
    return ResidentRepository(db_path)


def test_persist_resident(repo):
    """Required Test 1: Verify that a valid Resident can be stored successfully."""
    # Create a new Resident object in memory
    resident = Resident(
        first_name="Mochi",
        last_name="Cat",
        address="123 Alabang-Zapote Rd, Poblacion, Muntinlupa City",
        contact_number="09171234567",
        email="mochi.cat@example.com",
    )
    # Save the resident into SQLite
    saved_resident = repo.save(resident)
    # Make sure the save operation returned a valid resident object instead of None
    assert saved_resident is not None


def test_resident_receives_identifier(repo):
    """Required Test 2: Verify saved resident receives an auto-generated ID (int)."""
    resident = Resident(
        first_name="Boba",
        last_name="Doggo",
        address="456 Commerce Ave, Ayala Alabang, Muntinlupa City",
        contact_number="09189876543",
        email="boba.doggo@example.com",
    )
    # Before saving, the resident should not have an ID yet
    assert resident.id is None  
    # Save the resident to generate a database ID
    saved_resident = repo.save(resident)
    # Confirm that an ID was assigned and that it is an integer
    assert saved_resident.id is not None
    assert isinstance(saved_resident.id, int)


def test_retrieve_resident_by_id(repo):
    """Required Test 3: Retrieve saved resident using assigned ID."""
    resident = Resident(
        first_name="Peanut",
        last_name="Hamster",
        address="789 Montillano St, Alabang, Muntinlupa City",
        contact_number="09201112233",
        email="peanut.hamster@example.com",
    )
    # Save the resident first so it gets a database ID
    saved_resident = repo.save(resident)
    # Fetch the resident back out of the database using its new ID
    retrieved = repo.find_by_id(saved_resident.id)

    # Make sure it found a record and that its ID matches what we saved
    assert retrieved is not None
    assert retrieved.id == saved_resident.id


def test_resident_information_is_preserved(repo):
    """Required Test 4: Verify text integrity (like leading 0 in contact numbers)."""
    resident = Resident(
        first_name="Coco",
        last_name="Bunny",
        address="101 Soldiers Hills, Putatan, Muntinlupa City",
        contact_number="09170001122",
        email="coco.bunny@example.com",
        status="Active",
    )
    saved_resident = repo.save(resident)
    retrieved = repo.find_by_id(saved_resident.id)

    # Check every text field to ensure SQLite saved and returned exact data
    assert retrieved.first_name == "Coco"
    assert retrieved.last_name == "Bunny"
    assert retrieved.address == "101 Soldiers Hills, Putatan, Muntinlupa City"
    assert retrieved.contact_number == "09170001122"  # Retains leading zero
    assert retrieved.email == "coco.bunny@example.com"
    assert retrieved.status == "Active"


def test_active_status_is_preserved(repo):
    """Required Test 5: Verify default Active status stays correctly."""
    resident = Resident(
        first_name="Tofu",
        last_name="Kitten",
        address="202 Bruger Subdivision, Tunasan, Muntinlupa City",
        contact_number="09193334455",
        email="tofu.kitten@example.com",
    )
    saved_resident = repo.save(resident)
    retrieved = repo.find_by_id(saved_resident.id)

    # Verify that the default 'Active' status is saved and retrieved properly
    assert retrieved.status == "Active"


def test_missing_resident_returns_none(repo):
    """Required Test 6: Non-existent IDs return None without crashing."""
    # Look for a fake ID that definitely does not exist 
    result = repo.find_by_id(999999)
    # Verify the method safely gives us None instead of throwing an error
    assert result is None


def test_persistence_across_multiple_repository_instances(tmp_path):
    """Required Test 7: Verify real SQLite storage by fetching a new repo object."""
    db_file = tmp_path / "multi_inst_test.db"
    db_path = str(db_file)
    init_db(db_path)

    # Use the first repository connection to save a resident
    repo1 = ResidentRepository(db_path)
    resident = Resident(
        first_name="Matcha",
        last_name="Pug",
        address="303 East Service Rd, Sucat, Muntinlupa City",
        contact_number="09285556677",
        email="matcha.pug@example.com",
    )
    saved_resident = repo1.save(resident)

    # Open a brand new second repository connection to the same database file
    repo2 = ResidentRepository(db_path)
    retrieved = repo2.find_by_id(saved_resident.id)

    # Prove data was written to the actual database file and not just kept in memory
    assert retrieved is not None
    assert retrieved.first_name == "Matcha"


def test_sequential_residents_get_unique_ids(repo):
    """Student-Designed Test: Verify storing multiple residents back to back generates unique, sequential IDs.
    Ensures adding new residents gives them unique IDs so they don't overwrite existing ones or crash.
    """
    resident1 = Resident(
        first_name="Waffles",
        last_name="Corgi",
        address="123 Civic Drive, Filinvest City, Alabang, Muntinlupa City",
        contact_number="09170001111",
        email="waffles.corgi@example.com",
    )
    resident2 = Resident(
        first_name="Latte",
        last_name="Persian",
        address="456 Susana Heights, Tunasan, Muntinlupa City",
        contact_number="09180002222",
        email="latte.persian@example.com",
    )

    # Save two residents one after another
    saved1 = repo.save(resident1)
    saved2 = repo.save(resident2)

    # Make sure their IDs are different and that the second ID is 1 higher than the first
    assert saved1.id != saved2.id
    assert saved2.id == saved1.id + 1