# ==============================================================================
# Ticket T12: Presentation and integration tests for Resident Management UI.
# ==============================================================================

import pytest
from csms import create_app
from csms.db.database import init_db
from csms.models.resident import Resident
from csms.repositories.resident_repository import ResidentRepository

# Helper Functions ---


@pytest.fixture
def app_client(tmp_path):
    """Fixture providing a Flask test client with an isolated SQLite DB."""
    database_path = tmp_path / "t12-residents.sqlite"
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


# 14 Required Tests ---


def test_resident_management_page_loads_successfully(app_client):
    # Test 1: Resident Management Page Loads Successfully.
    client, _ = app_client
    response = client.get("/residents")
    assert response.status_code == 200
    assert b"Resident Management" in response.data


def test_resident_list_displays_persisted_residents(app_client):
    # Test 2: Resident List Displays Persisted Residents.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    repo.save(
        Resident(
            first_name="Juan",
            last_name="Cruz",
            address="Street 1",
            contact_number="09171234567",
            email="juan@example.com",
        )
    )

    response = client.get("/residents")
    assert response.status_code == 200
    assert b"Juan" in response.data
    assert b"Cruz" in response.data


def test_resident_search_uses_existing_search_behavior(app_client):
    # Test 3: Resident Search Uses Existing Search Behavior.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    repo.save(
        Resident(
            first_name="Maria",
            last_name="Santos",
            address="Street 1",
            contact_number="09171234567",
            email="maria@example.com",
        )
    )
    repo.save(
        Resident(
            first_name="Pedro",
            last_name="Penduko",
            address="Street 2",
            contact_number="09181234567",
            email="pedro@example.com",
        )
    )

    response = client.get("/residents?search=mar")
    assert response.status_code == 200
    assert b"Maria" in response.data
    assert b"Pedro" not in response.data


def test_blank_search_displays_all_residents(app_client):
    # Test 4: Blank Search Displays All Residents.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    repo.save(
        Resident(
            first_name="Ana",
            last_name="Reyes",
            address="Addr 1",
            contact_number="09171234567",
            email="ana@example.com",
        )
    )
    repo.save(
        Resident(
            first_name="Jose",
            last_name="Rizal",
            address="Addr 2",
            contact_number="09181234567",
            email="jose@example.com",
        )
    )

    response = client.get("/residents?search=%20%20")
    assert response.status_code == 200
    assert b"Ana" in response.data
    assert b"Jose" in response.data


def test_registration_form_is_accessible(app_client):
    # Test 5: Registration Form Is Accessible.
    client, _ = app_client
    response = client.get("/residents/register")
    assert response.status_code == 200
    assert b"Register Resident" in response.data
    assert b"first_name" in response.data


def test_valid_registration_persists_resident(app_client):
    # Test 6: Valid Registration Persists Resident.
    client, db_path = app_client
    response = client.post(
        "/residents/register",
        data={
            "first_name": "Juan",
            "last_name": "Luna",
            "address": "Manila",
            "contact_number": "09171234567",
            "email": "juan.luna@example.com",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Resident registered successfully." in response.data

    repo = ResidentRepository(db_path)
    all_residents = repo.find_all()
    assert len(all_residents) == 1
    assert all_residents[0].first_name == "Juan"
    assert all_residents[0].status == "Active"


def test_invalid_registration_shows_validation_feedback_and_does_not_persist(
    app_client,
):
    # Test 7: Invalid Registration Shows Validation Feedback and Does Not Persist.
    client, db_path = app_client
    response = client.post(
        "/residents/register",
        data={
            "first_name": "",  # Blank first name
            "last_name": "Luna",
            "address": "Manila",
            "contact_number": "09171234567",
            "email": "juan.luna@example.com",
        },
    )
    assert response.status_code == 400
    assert b"alert-error" in response.data or b"required" in response.data.lower() or b"error" in response.data.lower()

    repo = ResidentRepository(db_path)
    assert len(repo.find_all()) == 0


def test_edit_form_displays_existing_resident_information(app_client):
    # Test 8: Edit Form Displays Existing Resident Information.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    saved = repo.save(
        Resident(
            first_name="Andres",
            last_name="Bonifacio",
            address="Tondo",
            contact_number="09171234567",
            email="andres@example.com",
        )
    )

    response = client.get(f"/residents/{saved.id}/edit")
    assert response.status_code == 200
    assert b"Andres" in response.data
    assert b"Bonifacio" in response.data


def test_valid_update_persists_changes(app_client):
    # Test 9: Valid Update Persists Changes.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    saved = repo.save(
        Resident(
            first_name="Melchora",
            last_name="Aquino",
            address="Quezon City",
            contact_number="09171234567",
            email="melchora@example.com",
        )
    )

    response = client.post(
        f"/residents/{saved.id}/edit",
        data={
            "first_name": "Tandang",
            "last_name": "Sora",
            "address": "Quezon City",
            "contact_number": "09181234567",
            "email": "tandang.sora@example.com",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Resident information updated successfully." in response.data

    updated = repo.find_by_id(saved.id)
    assert updated.first_name == "Tandang"
    assert updated.last_name == "Sora"
    assert updated.status == "Active"


def test_invalid_update_does_not_modify_resident(app_client):
    # Test 10: Invalid Update Does Not Modify Resident.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    saved = repo.save(
        Resident(
            first_name="Emilio",
            last_name="Aguinaldo",
            address="Cavite",
            contact_number="09171234567",
            email="emilio@example.com",
        )
    )

    response = client.post(
        f"/residents/{saved.id}/edit",
        data={
            "first_name": "",  # Invalid blank
            "last_name": "Aguinaldo",
            "address": "Cavite",
            "contact_number": "09171234567",
            "email": "emilio@example.com",
        },
    )
    assert response.status_code == 400

    db_res = repo.find_by_id(saved.id)
    assert db_res.first_name == "Emilio"


def test_missing_resident_edit_is_handled_safely(app_client):
    # Test 11: Missing Resident Edit Is Handled Safely.
    client, _ = app_client
    response = client.get("/residents/99999/edit")
    assert response.status_code == 404
    assert b"404 - Not Found" in response.data


def test_active_resident_can_be_deactivated_through_interface(app_client):
    # Test 12: Active Resident Can Be Deactivated Through Interface.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    saved = repo.save(
        Resident(
            first_name="Apolinario",
            last_name="Mabini",
            address="Batangas",
            contact_number="09171234567",
            email="mabini@example.com",
        )
    )

    response = client.post(
        f"/residents/{saved.id}/deactivate",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Resident deactivated successfully." in response.data

    deactivated = repo.find_by_id(saved.id)
    assert deactivated.status == "Inactive"


def test_inactive_resident_remains_visible(app_client):
    # Test 13: Inactive Resident Remains Visible.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    repo.save(
        Resident(
            first_name="Marcelo",
            last_name="Del Pilar",
            address="Bulacan",
            contact_number="09171234567",
            email="marcelo@example.com",
            status="Inactive",
        )
    )

    response = client.get("/residents")
    assert response.status_code == 200
    assert b"Marcelo" in response.data
    assert b"Inactive" in response.data


def test_get_requests_do_not_deactivate_residents(app_client):
    # Test 14: GET Requests Do Not Deactivate Residents.
    client, db_path = app_client
    repo = ResidentRepository(db_path)
    saved = repo.save(
        Resident(
            first_name="Gobernador",
            last_name="Test",
            address="Address",
            contact_number="09171234567",
            email="get@example.com",
            status="Active",
        )
    )

    client.get("/residents")
    client.get(f"/residents?search={saved.first_name}")
    client.get(f"/residents/{saved.id}/edit")

    current = repo.find_by_id(saved.id)
    assert current.status == "Active"