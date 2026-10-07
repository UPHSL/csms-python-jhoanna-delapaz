'''
# Ticket T10: Service Request Status Service
# applies controlled status transition logic before persisting updates

'''

from typing import Optional
from src.csms.repositories.service_request_repository import ServiceRequestRepository
from src.csms.services.service_request_status_result import ServiceRequestStatusResult


class ServiceRequestStatusService:

    # define set of supported statuses 
    SUPPORTED_STATUSES = {"Pending", "In Progress", "Completed", "Cancelled"}

    # allowed state transitions
    ALLOWED_TRANSITIONS = {
        "Pending": {"In Progress", "Cancelled"},
        "In Progress": {"Completed", "Cancelled"},
        "Completed": set(),  # Terminal state
        "Cancelled": set(),  # Terminal state
    }

    def __init__(self, service_request_repository: Optional[ServiceRequestRepository] = None):
        # link repository dependency
        self.service_request_repository = (
            service_request_repository or ServiceRequestRepository()
        )

    def update_status(self, request_id: int, requested_status: str) -> ServiceRequestStatusResult:
        """processes status update while validating rules before touching persistence"""

        # step 1 - verify if requested target status is valid in workflow
        if requested_status not in self.SUPPORTED_STATUSES:
            return ServiceRequestStatusResult(
                success=False,
                unsupported_status=True,
            )

        # step 2 - get current record from repository
        existing_request = self.service_request_repository.find_by_id(request_id)
        if existing_request is None:
            return ServiceRequestStatusResult(
                success=False,
                not_found=True,
            )

        current_status = existing_request.status

        # step 3 - check if transition from current to requested state is allowed
        allowed_targets = self.ALLOWED_TRANSITIONS.get(current_status, set())
        if requested_status not in allowed_targets:
            return ServiceRequestStatusResult(
                success=False,
                invalid_transition=True,
            )

        # step 4 - persist valid status change
        self.service_request_repository.update_status(request_id, requested_status)

        # step 5 - retrieve updated request to confirm persisted state
        updated_request = self.service_request_repository.find_by_id(request_id)

        return ServiceRequestStatusResult(
            success=True,
            service_request=updated_request,
        )