'''
# Ticket T09: Service Request Submission Service 
# basically gathers and manages everything together 
# included parts are Service Request submission, validation, resident checks, and persistence

'''

from src.csms.models.service_request import ServiceRequest
from src.csms.services.service_request_submission_result import ServiceRequestSubmissionResult
from src.csms.services.service_request_validator import ServiceRequestValidator
from src.csms.repositories.resident_repository import ResidentRepository
from src.csms.repositories.service_request_repository import ServiceRequestRepository


class ServiceRequestSubmissionService:

    def __init__(
        self,
        validator: ServiceRequestValidator = None,
        resident_repository: ResidentRepository = None,
        service_request_repository: ServiceRequestRepository = None,
    ):
        self.validator = validator or ServiceRequestValidator()
        self.resident_repository = resident_repository or ResidentRepository()
        self.service_request_repository = (
            service_request_repository or ServiceRequestRepository()
        )

    def submit(self, service_request: ServiceRequest) -> ServiceRequestSubmissionResult:
        """Executes the complete submission workflow in a sequence"""

        # first step would be validating intrinsic service request data
        validation_errors = self.validator.validate(service_request)
        if validation_errors:
            return ServiceRequestSubmissionResult(
                success=False,
                errors=validation_errors,
            )

        # then it verifies if referenced resident exists
        resident = self.resident_repository.find_by_id(service_request.resident_id)
        if resident is None:
            return ServiceRequestSubmissionResult(
                success=False,
                resident_not_found=True,
            )

        # verify if resident status is Active
        if resident.status != "Active":
            return ServiceRequestSubmissionResult(
                success=False,
                resident_inactive=True,
            )

        # persist valid request and generate ID
        persisted_request = self.service_request_repository.save(service_request)

        # return successful submission result
        return ServiceRequestSubmissionResult(
            success=True,
            service_request=persisted_request,
        )