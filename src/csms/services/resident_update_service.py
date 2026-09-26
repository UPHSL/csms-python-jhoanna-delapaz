"""
# T06: reads an existing resident, keeps their ID and status, validates the new info
with T02, and saves the changes.

"""
from src.csms.models.resident import Resident
from src.csms.repositories.resident_repository import ResidentRepository
from src.csms.services.resident_validator import ResidentValidator
from src.csms.services.resident_update_result import ResidentUpdateResult


class ResidentUpdateService:

    def __init__(
        self,
        validator: ResidentValidator,
        repository: ResidentRepository,
    ) -> None:
        
        # Attach the T02 validator so we can check rules before saving
        self.validator = validator

        # Attach the T03/T06 database repository so we can read and write to SQLite
        self.repository = repository

    def update_resident(
        self,
        resident_id: int,
        first_name: str,
        last_name: str,
        address: str,
        contact_number: str,
        email: str,
    ) -> ResidentUpdateResult:
        """T06: Updates an existing resident's personal details while preserving ID and status. """

        # Look up existing resident
        existing_resident = self.repository.find_by_id(resident_id)
        if existing_resident is None:
            return ResidentUpdateResult.resident_not_found()

        # Build updated user preserving ID and existing status
        updated_candidate = Resident(
            id=existing_resident.id,
            first_name=first_name,
            last_name=last_name,
            address=address,
            contact_number=contact_number,
            email=email,
            status=existing_resident.status,  # Preserve existing status strictly
        )

        # Validate updated user using T02 ResidentValidator
        errors = self.validator.validate(updated_candidate)
        if errors:
            return ResidentUpdateResult.validation_failed(errors)

        # Persist valid changes to repository
        persisted_resident = self.repository.update(updated_candidate)

        if persisted_resident is None:
            return ResidentUpdateResult.resident_not_found()

        return ResidentUpdateResult.successful(persisted_resident)

    """
    This service does the following steps in order:
        1. Find existing resident by ID (returns not_found if missing)
        2. Keep original ID and status 
        3. Validate changes using T02 ResidentValidator
        4. Save to database only if completely valid
        5. Return the result status object
    """