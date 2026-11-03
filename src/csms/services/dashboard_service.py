'''
# T14: CSMS Dashboard Application Service
# for composing read-only operational aggregate metrics and recent requests

'''
from dataclasses import dataclass
from typing import Optional
from src.csms.models.service_request import ServiceRequest
from src.csms.repositories.resident_repository import ResidentRepository
from src.csms.repositories.service_request_repository import ServiceRequestRepository


@dataclass
class DashboardSummary:
    """Data transfer object holding read-only dashboard metrics."""
    total_residents: int
    active_residents: int
    inactive_residents: int
    total_service_requests: int
    pending_requests: int
    in_progress_requests: int
    completed_requests: int
    cancelled_requests: int
    open_service_requests: int
    recent_service_requests: list[ServiceRequest]


class DashboardService:
    def __init__(
        self,
        resident_repository: ResidentRepository,
        service_request_repository: ServiceRequestRepository,
    ):
        self.resident_repository = resident_repository
        self.service_request_repository = service_request_repository

    def get_summary(self) -> DashboardSummary:
        """Gets aggregate counts from repositories and derives open requests."""
        # Resident aggregate metrics
        total_residents = self.resident_repository.count_all()
        active_residents = self.resident_repository.count_by_status("Active")
        inactive_residents = self.resident_repository.count_by_status("Inactive")

        # Service Request aggregate metrics
        total_service_requests = self.service_request_repository.count_all()
        pending_requests = self.service_request_repository.count_by_status("Pending")
        in_progress_requests = self.service_request_repository.count_by_status("In Progress")
        completed_requests = self.service_request_repository.count_by_status("Completed")
        cancelled_requests = self.service_request_repository.count_by_status("Cancelled")

        # metric: Open = Pending plus In Progress
        open_service_requests = pending_requests + in_progress_requests

        # Recent 5 requests using dateRequested DESC, id DESC
        recent_service_requests = self.service_request_repository.find_recent(limit=5)

        return DashboardSummary(
            total_residents=total_residents,
            active_residents=active_residents,
            inactive_residents=inactive_residents,
            total_service_requests=total_service_requests,
            pending_requests=pending_requests,
            in_progress_requests=in_progress_requests,
            completed_requests=completed_requests,
            cancelled_requests=cancelled_requests,
            open_service_requests=open_service_requests,
            recent_service_requests=recent_service_requests,
        )