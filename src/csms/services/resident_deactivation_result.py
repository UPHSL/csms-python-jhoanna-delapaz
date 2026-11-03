"""
# T07: Result file/object for resident deactivation operations.
possible outputs: Just Deactivated, Already Inactive, and Resident Not Found.
"""
from typing import Optional
from src.csms.models.resident import Resident


class ResidentDeactivationResult:

    def __init__(
        self,
        success: bool,
        resident: Optional[Resident] = None,
        already_inactive: bool = False,
        not_found: bool = False,
    ) -> None:
        # True if the operation succeeded overall (deactivated or already inactive)
        self.success = success

        # Holds the persisted Resident object if found, otherwise None
        self.resident = resident

        # True if the resident was already inactive before this request
        self.already_inactive = already_inactive

        # True if no resident exists with the provided ID
        self.not_found = not_found

    @classmethod
    def deactivated(cls, resident: Resident) -> "ResidentDeactivationResult":
        """method: Resident was Active and is now changed to Inactive."""
        return cls(
            success=True,
            resident=resident,
            already_inactive=False,
            not_found=False,
        )

    @classmethod
    def was_already_inactive(
        cls, resident: Resident
    ) -> "ResidentDeactivationResult":
        """method: Resident was already Inactive (no change needed)."""
        return cls(
            success=True,
            resident=resident,
            already_inactive=True,
            not_found=False,
        )

    @classmethod
    def resident_not_found(cls) -> "ResidentDeactivationResult":
        """method: Resident ID does not exist (in persistence)"""
        return cls(
            success=False,
            resident=None,
            already_inactive=False,
            not_found=True,
        )