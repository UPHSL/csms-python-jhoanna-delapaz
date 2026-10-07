"""
Ticket T08: Define Service Request Domain Model

"""

# The class for the service request model ---------------------------------
class ServiceRequest:

    def __init__(
        self,
        resident_id,
        service_type,
        description,
        date_requested,
        status="Pending",
        id=None,
    ):
        # Save each information piece onto the object so it can be accessed later (T08).
        self.id = id
        self.resident_id = resident_id
        self.service_type = service_type
        self.description = description
        self.date_requested = date_requested
        self.status = status