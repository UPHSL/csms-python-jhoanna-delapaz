"""
# T07: soft deactivation service of a resident.
Checks existence, handles already-inactive status, updates status to Inactive,
and preserves all info and identity.
"""

from src.csms.repositories.resident_repository import ResidentRepository
from src.csms.services.resident_deactivation_result import (
    ResidentDeactivationResult,
)


class ResidentDeactivationService:

    def __init__(self, repository: ResidentRepository) -> None:
        # Save T03 repository instance for database access
        self.repository = repository

    def deactivate_resident(
        self, resident_id: int
    ) -> ResidentDeactivationResult:
        """changes an Active resident to Inactive by ID."""

        # Look up existing resident in database by ID
        existing_resident = self.repository.find_by_id(resident_id)
        if existing_resident is None:
            # Resident ID does not exist, return not-found
            return ResidentDeactivationResult.resident_not_found()

        # Check current status
        if existing_resident.status == "Inactive":
            # Resident is already inactive, return already-inactive 
            return ResidentDeactivationResult.was_already_inactive(
                existing_resident
            )

        # Deactivate in database (changes status to Inactive)
        self.repository.deactivate(resident_id)

        # Fetch updated resident record to confirm persisted state
        updated_resident = self.repository.find_by_id(resident_id)

        # Return successful deactivation result
        return ResidentDeactivationResult.deactivated(updated_resident)