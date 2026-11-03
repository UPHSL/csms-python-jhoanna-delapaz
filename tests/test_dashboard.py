# ==============================================================================
# Ticket T14: CSMS Dashboard Operational Summary and Aggregate Querying Tests.
# ==============================================================================

from datetime import date
import pytest
from csms import create_app
from csms.db.database import init_db
from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository

# Helper Functions ---


@pytest.fixture
def app_client(tmp_path):
    """Fixture providing a Flask test client with an isolated SQLite DB."""
    database_path = tmp_path / "t14-dashboard.sqlite"
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


# 15 Required Tests ---


def test_dashboard_loads_successfully(app_client):
    # Test 1: Dashboard Loads Successfully.
    client, _ = app_client
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Dashboard" in response.data


def test_empty_dashboard_displays_zero_counts(app_client):
    # Test 2: Empty Dashboard Displays Zero Counts.
    client, _ = app_client
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Total Residents" in response.data
    assert b"No Service Requests available." in response.data


def test_total_resident_count_is_correct(app_client):
    # Test 3: Total Resident Count Is Correct.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    res_repo.save(
        Resident(
            first_name="John",
            last_name="Doe",
            address="123 St",
            contact_number="09171234567",
            email="john@example.com",
        )
    )
    res_repo.save(
        Resident(
            first_name="Jane",
            last_name="Smith",
            address="456 St",
            contact_number="09177654321",
            email="jane@example.com",
        )
    )

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b'id="total-residents">2</span>' in response.data


def test_resident_status_counts_are_correct(app_client):
    # Test 4: Resident Status Counts Are Correct.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    res_repo.save(
        Resident(
            first_name="Active",
            last_name="One",
            address="123 St",
            contact_number="09171234567",
            email="a1@example.com",
        )
    )
    res_repo.save(
        Resident(
            first_name="Active",
            last_name="Two",
            address="456 St",
            contact_number="09177654321",
            email="a2@example.com",
        )
    )
    r3 = res_repo.save(
        Resident(
            first_name="Inactive",
            last_name="Three",
            address="789 St",
            contact_number="09181112222",
            email="i3@example.com",
        )
    )
    res_repo.deactivate(r3.id)

    response = client.get("/dashboard")
    assert b'id="total-residents">3</span>' in response.data
    assert b'id="active-residents">2</span>' in response.data
    assert b'id="inactive-residents">1</span>' in response.data


def test_total_service_request_count_is_correct(app_client):
    # Test 5: Total Service Request Count Is Correct.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="Plumbing",
            description="Leak",
            date_requested=date(2026, 10, 1),
            status="Pending",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="Electrical",
            description="Power outage",
            date_requested=date(2026, 10, 2),
            status="In Progress",
        )
    )

    response = client.get("/dashboard")
    assert b'id="total-service-requests">2</span>' in response.data


def test_service_request_status_counts_are_correct(app_client):
    # Test 6: Service Request Status Counts Are Correct.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P1",
            description="D1",
            date_requested=date(2026, 10, 1),
            status="Pending",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P2",
            description="D2",
            date_requested=date(2026, 10, 2),
            status="In Progress",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P3",
            description="D3",
            date_requested=date(2026, 10, 3),
            status="Completed",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P4",
            description="D4",
            date_requested=date(2026, 10, 4),
            status="Cancelled",
        )
    )

    response = client.get("/dashboard")
    assert b'id="pending-requests">1</span>' in response.data
    assert b'id="in-progress-requests">1</span>' in response.data
    assert b'id="completed-requests">1</span>' in response.data
    assert b'id="cancelled-requests">1</span>' in response.data


def test_service_request_counts_reconcile(app_client):
    # Test 7: Service Request Counts Reconcile.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P1",
            description="D1",
            date_requested=date(2026, 10, 1),
            status="Pending",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P2",
            description="D2",
            date_requested=date(2026, 10, 2),
            status="Completed",
        )
    )

    response = client.get("/dashboard")
    assert b'id="total-service-requests">2</span>' in response.data
    assert b'id="pending-requests">1</span>' in response.data
    assert b'id="completed-requests">1</span>' in response.data


def test_open_request_count_is_correct(app_client):
    # Test 8: Open Request Count Is Correct.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P1",
            description="D1",
            date_requested=date(2026, 10, 1),
            status="Pending",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P2",
            description="D2",
            date_requested=date(2026, 10, 2),
            status="In Progress",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P3",
            description="D3",
            date_requested=date(2026, 10, 3),
            status="Completed",
        )
    )

    response = client.get("/dashboard")
    assert b'id="open-service-requests">2</span>' in response.data


def test_resident_deactivation_is_reflected(app_client):
    # Test 9: Resident Deactivation Is Reflected.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="John",
            last_name="Doe",
            address="123 St",
            contact_number="09171234567",
            email="john@example.com",
        )
    )

    resp1 = client.get("/dashboard")
    assert b'id="active-residents">1</span>' in resp1.data
    assert b'id="inactive-residents">0</span>' in resp1.data

    res_repo.deactivate(r.id)

    resp2 = client.get("/dashboard")
    assert b'id="active-residents">0</span>' in resp2.data
    assert b'id="inactive-residents">1</span>' in resp2.data


def test_service_request_transition_is_reflected(app_client):
    # Test 10: Service Request Transition Is Reflected.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr = sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P1",
            description="D1",
            date_requested=date(2026, 10, 1),
            status="Pending",
        )
    )

    resp1 = client.get("/dashboard")
    assert b'id="pending-requests">1</span>' in resp1.data
    assert b'id="in-progress-requests">0</span>' in resp1.data

    sr_repo.update_status(sr.id, "In Progress")

    resp2 = client.get("/dashboard")
    assert b'id="pending-requests">0</span>' in resp2.data
    assert b'id="in-progress-requests">1</span>' in resp2.data


def test_terminal_transition_updates_open_count(app_client):
    # Test 11: Terminal Transition Updates Open Count.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr = sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="P1",
            description="D1",
            date_requested=date(2026, 10, 1),
            status="In Progress",
        )
    )

    resp1 = client.get("/dashboard")
    assert b'id="open-service-requests">1</span>' in resp1.data

    sr_repo.update_status(sr.id, "Completed")

    resp2 = client.get("/dashboard")
    assert b'id="open-service-requests">0</span>' in resp2.data


def test_recent_requests_return_no_more_than_five(app_client):
    # Test 12: Recent Requests Return No More Than Five.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    for i in range(7):
        sr_repo.save(
            ServiceRequest(
                resident_id=r.id,
                service_type=f"Type {i}",
                description=f"Desc {i}",
                date_requested=date(2026, 10, i + 1),
                status="Pending",
            )
        )

    response = client.get("/dashboard")
    assert response.data.count(b"View") == 5


def test_recent_requests_use_correct_ordering(app_client):
    # Test 13: Recent Requests Use Correct Ordering.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr1 = sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="Old",
            description="D1",
            date_requested=date(2026, 10, 1),
            status="Pending",
        )
    )
    sr2 = sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="New Same Date 1",
            description="D2",
            date_requested=date(2026, 10, 10),
            status="Pending",
        )
    )
    sr3 = sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="New Same Date 2",
            description="D3",
            date_requested=date(2026, 10, 10),
            status="Pending",
        )
    )

    response = client.get("/dashboard")
    content = response.data.decode("utf-8")
    pos_sr3 = content.find("New Same Date 2")
    pos_sr2 = content.find("New Same Date 1")
    pos_sr1 = content.find("Old")

    assert pos_sr3 < pos_sr2 < pos_sr1


def test_terminal_requests_may_appear_in_recent_results(app_client):
    # Test 14: Terminal Requests May Appear in Recent Results.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="Finished Work",
            description="Done",
            date_requested=date(2026, 10, 15),
            status="Completed",
        )
    )

    response = client.get("/dashboard")
    assert b"Finished Work" in response.data
    assert b"Completed" in response.data


def test_dashboard_get_does_not_modify_persistence(app_client):
    # Test 15: Dashboard GET Does Not Modify Persistence.
    client, db_path = app_client
    res_repo = ResidentRepository(db_path)
    sr_repo = ServiceRequestRepository(db_path)

    r = res_repo.save(
        Resident(
            first_name="Test",
            last_name="User",
            address="123 St",
            contact_number="09171234567",
            email="t@example.com",
        )
    )
    sr = sr_repo.save(
        ServiceRequest(
            resident_id=r.id,
            service_type="Test",
            description="Test",
            date_requested=date(2026, 10, 1),
            status="Pending",
        )
    )

    client.get("/dashboard")
    client.get("/dashboard")

    assert res_repo.count_all() == 1
    assert sr_repo.count_all() == 1
    assert sr_repo.find_by_id(sr.id).status == "Pending"