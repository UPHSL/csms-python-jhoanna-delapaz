"""
# T06: This object represents the outcome of updating a resident.
It returns one of three results: Success, Validation Failure, or Resident Not Found

"""
from typing import Optional
from src.csms.models.resident import Resident


class ResidentUpdateResult:

    def __init__(
        self,
        success: bool,
        resident: Optional[Resident] = None,
        errors: Optional[list[str]] = None,
        not_found: bool = False,
    ) -> None:
        # True if update succeeded
        self.success = success

        # Holds the updated Resident object if successful (otherwise None)
        self.resident = resident

        # List of invalid field names if validation fails
        self.errors = errors if errors is not None else []

        # True if no resident exists with the provided ID
        self.not_found = not_found

    @classmethod
    def successful(cls, resident: Resident) -> "ResidentUpdateResult":
        """method for a successful update."""
        return cls(success=True, resident=resident, errors=[], not_found=False)

    @classmethod
    def validation_failed(cls, errors: list[str]) -> "ResidentUpdateResult":
        """method for when T02 validation fails."""
        return cls(success=False, resident=None, errors=errors, not_found=False)

    @classmethod
    def resident_not_found(cls) -> "ResidentUpdateResult":
        """method for when the resident ID does not exist."""
        return cls(success=False, resident=None, errors=[], not_found=True)