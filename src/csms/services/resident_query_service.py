# ==============================================================================
# Ticket T05: Resident Query Service
# Coordinates Resident listing and name searching application logic.
# ==============================================================================

from src.csms.models.resident import Resident
from src.csms.repositories.resident_repository import (
    ResidentRepository,
)

class ResidentQueryService:
    def __init__(
        self,
        repository: ResidentRepository,
    ) -> None:
        self.repository = repository

# --- List All Residents ---
    def list_residents(
        self,
    ) -> list[Resident]:
        return self.repository.find_all()
    
# --- Search Residents ---
    def search_residents(
        self,
        search_term: str | None,
    ) -> list[Resident]:
        normalized_search_term = (
            ""
            if search_term is None
            else search_term.strip()
        )

        if not normalized_search_term:
            return self.list_residents()

        return self.repository.search_by_name(
            normalized_search_term
        )