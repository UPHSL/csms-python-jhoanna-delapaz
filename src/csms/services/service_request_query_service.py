'''
# Ticket T11: Service Request Query Service
# Coordinates listing, viewing by ID, text search, and status filtering logic.
'''

from typing import Optional
from src.csms.models.service_request import ServiceRequest
from src.csms.repositories.service_request_repository import ServiceRequestRepository

VALID_STATUSES = {"Pending", "In Progress", "Completed", "Cancelled"}


class ServiceRequestQueryService:

    def __init__(self, repository: ServiceRequestRepository) -> None:
        self.repository = repository

    def list_service_requests(self) -> list[ServiceRequest]:
        """Returns all persisted Service Requests in dateRequested DESC, id DESC order."""
        return self.repository.find_all()

    def view_service_request(self, request_id: int) -> Optional[ServiceRequest]:
        """Retrieves a single Service Request by ID, returning None safely if not found."""
        return self.repository.find_by_id(request_id)

    def search_service_requests(
        self,
        search_term: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> list[ServiceRequest]:
        """
        Normalizes search term, validates status filter, and queries persistence layer.
        - Blank text terms are treated as list all.
        - Whitespace is trimmed from search inputs.
        - Invalid/unsupported non-empty status filters raise a ValueError or return empty collection.
        """
        # Normalize text search input (ignore leading whitespace)
        normalized_search_term = (
            search_term.strip() if search_term and search_term.strip() else None
        )

        # Normalize status filter input
        normalized_status_filter = (
            status_filter.strip() if status_filter and status_filter.strip() else None
        )

        # Validate unsupported status filters
        if normalized_status_filter and normalized_status_filter not in VALID_STATUSES:
            # Return empty collection for unsupported status filters
            return []

        return self.repository.search(
            search_term=normalized_search_term,
            status_filter=normalized_status_filter,
        )