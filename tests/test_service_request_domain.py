# ==============================================================================
# Ticket T08: Unit tests for Service Request domain model
# ==============================================================================

from datetime import date
from src.csms.models.service_request import ServiceRequest


def test_service_request_can_be_created():
    # Test 1: Service Request Can Be Created 
    # Create a new service request with basic valid details
    request = ServiceRequest(
        resident_id=25,
        service_type="Barangay Clearance",
        description="Request for employment requirement",
        date_requested=date(2026, 9, 28),
    )

    # Check that the object was created successfully
    assert request is not None


def test_service_request_information_is_accessible():
    # Test 2: Service Request Information Is Accessible 
    # Create a service request with specific field values
    request = ServiceRequest(
        resident_id=25,
        service_type="Certificate Request",
        description="Need certificate for scholarship",
        date_requested=date(2026, 9, 28),
    )

    # Verify that every stored field can be read correctly 
    assert request.resident_id == 25
    assert request.service_type == "Certificate Request"
    assert request.description == "Need certificate for scholarship"
    assert request.date_requested == date(2026, 9, 28)


def test_resident_id_is_preserved():
    # Test 3: Resident ID Is Preserved 
    # Create a request linked to resident ID 25
    request = ServiceRequest(
        resident_id=25,
        service_type="Permit Request",
        description="Business permit requirement",
        date_requested=date(2026, 9, 28),
    )

    # check if the resident_id stays without being altered
    assert request.resident_id == 25


def test_new_service_request_has_an_unassigned_id():
    # Test 4: New Service Request Has an Unassigned ID 
    # Create a brand new service request without passing an id
    request = ServiceRequest(
        resident_id=10,
        service_type="Community Assistance",
        description="Cash assistance",
        date_requested=date(2026, 9, 28),
    )

    # Verify that the id defaults to None before persistence
    assert request.id is None


def test_new_service_request_defaults_to_pending():
    # Test 5: New Service Request Defaults to Pending
    # Create a request without passing a custom status argument
    request = ServiceRequest(
        resident_id=15,
        service_type="Barangay Clearance",
        description="Business permit renewal",
        date_requested=date(2026, 9, 28),
    )

    # Check that the initial status defaults to "Pending"
    assert request.status == "Pending"


def test_service_request_information_is_independent_between_objects():
    # Test 6: Service Request Information Is Independent Between Objects 
    # Create the first service request object
    req1 = ServiceRequest(
        resident_id=1,
        service_type="Barangay Clearance",
        description="First request",
        date_requested=date(2026, 9, 28),
    )

    # the second independent service request with different details
    req2 = ServiceRequest(
        resident_id=2,
        service_type="Community Assistance",
        description="Second request",
        date_requested=date(2026, 9, 29),
    )

    # Check that the first request still holds its own data
    assert req1.resident_id == 1
    assert req1.service_type == "Barangay Clearance"
    assert req1.description == "First request"
    assert req1.date_requested == date(2026, 9, 28)

    # Check that the second request holds its separate data
    assert req2.resident_id == 2
    assert req2.service_type == "Community Assistance"
    assert req2.description == "Second request"
    assert req2.date_requested == date(2026, 9, 29)