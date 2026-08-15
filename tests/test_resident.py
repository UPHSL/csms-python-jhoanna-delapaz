from csms.models.resident import Resident

# TEST 1: Resident Creation
def test_resident_creation():
    resident = Resident(
        id=1,
        first_name="Jhoanna",
        last_name="Dela Paz",
        address="Tunasan, Muntinlupa",
        contact_number="09395030502",
        email="delapaz.jhoanna@ymail.com"
    )
    if resident is None:
        raise ValueError("Test failed: Resident not created!")

# TEST 2: Resident Information Access
def test_resident_information_access():
    resident = Resident(
        id=1,
        first_name="Jhoanna",
        last_name="Dela Paz",
        address="Tunasan, Muntinlupa",
        contact_number="09395030502",
        email="delapaz.jhoanna@ymail.com"
    )
    if resident.id != 1:
        raise ValueError("Test failed: ID does not match!")
    if resident.first_name != "Jhoanna":
        raise ValueError("Test failed: Incorrect First Name!")
    if resident.last_name != "Dela Paz":
        raise ValueError("Test failed: Incorrect Last Name!")
    if resident.address != "Tunasan, Muntinlupa":
        raise ValueError("Test failed: Address does not match!")
    if resident.contact_number != "09395030502":
        raise ValueError("Test failed: Contact number does not match!")
    if resident.email != "delapaz.jhoanna@ymail.com":
        raise ValueError("Test failed: Email does not match!")

# TEST 3: Resident Status
def test_resident_status():
    resident = Resident(
        id=1,
        first_name="Jhoanna",
        last_name="Dela Paz",
        address="Tunasan, Muntinlupa",
        contact_number="09395030502",
        email="delapaz.jhoanna@ymail.com"
    )
    if resident.status != "Active":
        raise ValueError("Test failed: Status should be Active! (Default)")