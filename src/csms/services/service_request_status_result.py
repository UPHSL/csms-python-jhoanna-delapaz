'''
# Ticket T10: Service Request Status Result
# gathers the output status flags and data of a status update attempt

'''

class ServiceRequestStatusResult:

    def __init__(
        self,
        success: bool,
        service_request=None,
        not_found: bool = False,
        unsupported_status: bool = False,
        invalid_transition: bool = False,
    ):
        # set to true if state transition succeeded and was saved
        self.success = success

        # carries updated ServiceRequest domain object on success
        self.service_request = service_request

        # true if target service_request id does not exist
        self.not_found = not_found

        # true if requested target status is not in supported list
        self.unsupported_status = unsupported_status

        # true if target transition is not allowed by workflow state rules
        self.invalid_transition = invalid_transition