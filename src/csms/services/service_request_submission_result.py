'''
# Ticket T09: Service Request Submission Result
# covers the outcome of a Service Request submission operation

'''

class ServiceRequestSubmissionResult:

    def __init__(
        self,
        success,
        service_request=None,
        errors=None,
        resident_not_found=False,
        resident_inactive=False,
    ):
        # true if submission succeeded and request was persisted
        self.success = success

        # persisted ServiceRequest instance with generated ID (or None)
        self.service_request = service_request

        # list or dictionary of intrinsic validation errors (if any)
        self.errors = errors if errors is not None else []

        # true if referenced resident_id does not exist in persistence
        self.resident_not_found = resident_not_found

        # true if referenced resident exists but status is Inactive
        self.resident_inactive = resident_inactive