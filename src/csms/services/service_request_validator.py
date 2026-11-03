'''
# Ticket T09: Service Request Data Validator
# checks and verifies intrinsic Service Request data prior to persistence

'''

from datetime import date
from src.csms.models.service_request import ServiceRequest


class ServiceRequestValidator:

    def validate(self, service_request: ServiceRequest) -> list[str]:
        """returns a list of field names that fail"""
        errors = []

        # ID must be unassigned (None) before persistence
        if service_request.id is not None:
            errors.append("id")

        # resident_id must be present and a positive integer
        if not self._is_valid_resident_id(service_request.resident_id):
            errors.append("resident_id")

        # service_type must be present and non-whitespace
        if self._is_blank(service_request.service_type):
            errors.append("service_type")

        # description must be present and non-whitespace
        if self._is_blank(service_request.description):
            errors.append("description")

        # date_requested must be present and a valid date object
        if not self._is_valid_date(service_request.date_requested):
            errors.append("date_requested")

        # initial status must be "Pending"
        if service_request.status != "Pending":
            errors.append("status")

        return errors

    def is_valid(self, service_request: ServiceRequest) -> bool:
        # becomes true if the request passes all validation rules
        return len(self.validate(service_request)) == 0

    @staticmethod
    def _is_blank(value: object) -> bool:
        # check if value is missing, not a string, or whitespace-only 
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _is_valid_resident_id(value: object) -> bool:
        # check if resident_id is a positive integer 
        return isinstance(value, int) and not isinstance(value, bool) and value > 0

    @staticmethod
    def _is_valid_date(value: object) -> bool:
        # check if date_requested is a valid date instance 
        return isinstance(value, date)