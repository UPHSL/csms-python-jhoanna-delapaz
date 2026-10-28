"""Web routes for the CSMS user interface."""

from datetime import datetime
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from csms.models.resident import Resident
from csms.models.service_request import ServiceRequest
from csms.repositories.resident_repository import ResidentRepository
from csms.repositories.service_request_repository import ServiceRequestRepository
from csms.services.resident_deactivation_service import ResidentDeactivationService
from csms.services.resident_query_service import ResidentQueryService
from csms.services.resident_registration_service import ResidentRegistrationService
from csms.services.resident_update_service import ResidentUpdateService
from csms.services.resident_validator import ResidentValidator
from csms.services.service_request_query_service import ServiceRequestQueryService
from csms.services.service_request_status_service import ServiceRequestStatusService
from csms.services.service_request_submission_service import ServiceRequestSubmissionService

main_blueprint = Blueprint("main", __name__)


# Helper Functions ---


def _get_database_path() -> str:
    """Helper function to obtain the active SQLite database path from app config."""
    return str(current_app.config.get("DATABASE_PATH", "csms.sqlite"))


def _get_repository() -> ResidentRepository:
    """Helper function to instantiate ResidentRepository."""
    return ResidentRepository(_get_database_path())


def _get_query_service() -> ResidentQueryService:
    """Helper function to instantiate ResidentQueryService."""
    repo = _get_repository()
    return ResidentQueryService(repo)


def _get_registration_service() -> ResidentRegistrationService:
    """Helper function to instantiate ResidentRegistrationService."""
    repo = _get_repository()
    validator = ResidentValidator()
    return ResidentRegistrationService(validator, repo)


def _get_update_service() -> ResidentUpdateService:
    """Helper function to instantiate ResidentUpdateService."""
    repo = _get_repository()
    validator = ResidentValidator()
    return ResidentUpdateService(validator, repo)


def _get_deactivation_service() -> ResidentDeactivationService:
    """Helper function to instantiate ResidentDeactivationService."""
    repo = _get_repository()
    return ResidentDeactivationService(repo)


def _get_service_request_repository() -> ServiceRequestRepository:
    """Helper function to instantiate ServiceRequestRepository."""
    return ServiceRequestRepository(_get_database_path())


def _get_service_request_query_service() -> ServiceRequestQueryService:
    """Helper function to instantiate ServiceRequestQueryService."""
    repo = _get_service_request_repository()
    return ServiceRequestQueryService(repo)


def _get_service_request_submission_service() -> ServiceRequestSubmissionService:
    """Helper function to instantiate ServiceRequestSubmissionService."""
    sr_repo = _get_service_request_repository()
    res_repo = _get_repository()
    return ServiceRequestSubmissionService(
        service_request_repository=sr_repo,
        resident_repository=res_repo,
    )


def _get_service_request_status_service() -> ServiceRequestStatusService:
    """Helper function to instantiate ServiceRequestStatusService."""
    repo = _get_service_request_repository()
    return ServiceRequestStatusService(service_request_repository=repo)


# Routes ---


@main_blueprint.get("/")
def index() -> str:
    """Display the Sprint 0 welcome page."""
    return render_template(
        "index.html",
        application_name=current_app.config["APP_NAME"],
        application_version=current_app.config["APP_VERSION"],
        current_sprint=current_app.config["CURRENT_SPRINT"],
    )


@main_blueprint.get("/health")
def health():
    """Return a simple application health response."""
    return jsonify(
        {
            "application": current_app.config["APP_NAME"],
            "status": "ok",
            "version": current_app.config["APP_VERSION"],
        }
    )


# T12: Resident Management UI Routes ---


@main_blueprint.get("/residents")
def list_residents():
    """Display resident management page with search capability using T05 query service."""
    search_term = request.args.get("search", "")
    query_service = _get_query_service()

    if search_term and search_term.strip():
        residents = query_service.search_residents(search_term)
    else:
        residents = query_service.list_residents()

    return render_template(
        "residents/index.html",
        residents=residents,
        search_term=search_term,
    )


@main_blueprint.get("/residents/register")
def register_resident_form():
    """Display the resident registration form."""
    return render_template("residents/register.html", errors=[], form_data={})


@main_blueprint.post("/residents/register")
def register_resident_submit():
    """Process resident registration submission via T04 registration service."""
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    address = request.form.get("address", "").strip()
    contact_number = request.form.get("contact_number", "").strip()
    email = request.form.get("email", "").strip()

    candidate = Resident(
        first_name=first_name,
        last_name=last_name,
        address=address,
        contact_number=contact_number,
        email=email,
    )

    registration_service = _get_registration_service()
    result = registration_service.register_resident(candidate)

    if result.success:
        flash("Resident registered successfully.", "success")
        return redirect(url_for("main.list_residents"))

    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "contact_number": contact_number,
        "email": email,
    }
    return (
        render_template(
            "residents/register.html",
            errors=result.errors,
            form_data=form_data,
        ),
        400,
    )


@main_blueprint.get("/residents/<int:resident_id>/edit")
def edit_resident_form(resident_id: int):
    """Display edit form prefilled with resident information or handle missing resident safely."""
    repo = _get_repository()
    resident = repo.find_by_id(resident_id)

    if resident is None:
        return (
            render_template(
                "residents/not_found.html",
                message=f"Resident with ID {resident_id} was not found.",
            ),
            404,
        )

    form_data = {
        "first_name": resident.first_name,
        "last_name": resident.last_name,
        "address": resident.address,
        "contact_number": resident.contact_number,
        "email": resident.email,
    }

    return render_template(
        "residents/edit.html",
        resident=resident,
        errors=[],
        form_data=form_data,
    )


@main_blueprint.post("/residents/<int:resident_id>/edit")
def edit_resident_submit(resident_id: int):
    """Process resident update submission via T06 update service."""
    repo = _get_repository()
    existing_resident = repo.find_by_id(resident_id)

    if existing_resident is None:
        return (
            render_template(
                "residents/not_found.html",
                message=f"Resident with ID {resident_id} was not found.",
            ),
            404,
        )

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    address = request.form.get("address", "").strip()
    contact_number = request.form.get("contact_number", "").strip()
    email = request.form.get("email", "").strip()

    update_service = _get_update_service()
    result = update_service.update_resident(
        resident_id=resident_id,
        first_name=first_name,
        last_name=last_name,
        address=address,
        contact_number=contact_number,
        email=email,
    )

    if result.success:
        flash("Resident information updated successfully.", "success")
        return redirect(url_for("main.list_residents"))

    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "contact_number": contact_number,
        "email": email,
    }

    return (
        render_template(
            "residents/edit.html",
            resident=existing_resident,
            errors=result.errors,
            form_data=form_data,
        ),
        400,
    )


@main_blueprint.post("/residents/<int:resident_id>/deactivate")
def deactivate_resident_submit(resident_id: int):
    """Process resident deactivation via T07 deactivation service."""
    deactivation_service = _get_deactivation_service()
    result = deactivation_service.deactivate_resident(resident_id)

    if getattr(result, "success", False) or getattr(result, "already_inactive", False):
        flash("Resident deactivated successfully.", "success")
    else:
        flash("Resident not found.", "error")

    return redirect(url_for("main.list_residents"))


# T13: Service Request Management UI Routes ---


@main_blueprint.get("/service-requests")
def list_service_requests():
    """Display service request management page with search and status filtering via T11 query service."""
    search_term = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    query_service = _get_service_request_query_service()

    service_requests = query_service.search_service_requests(
        search_term=search_term if search_term else None,
        status_filter=status_filter if status_filter else None,
    )

    return render_template(
        "service_requests/index.html",
        service_requests=service_requests,
        search_term=search_term,
        selected_status=status_filter,
    )


@main_blueprint.get("/service-requests/new")
def new_service_request():
    """Display the new service request submission form."""
    return render_template("service_requests/new.html", errors=[], form_data={}, global_error=None)


@main_blueprint.post("/service-requests/new")
def submit_service_request():
    """Process service request submission via T09 submission service."""
    resident_id_raw = request.form.get("resident_id", "").strip()
    service_type = request.form.get("service_type", "").strip()
    description = request.form.get("description", "").strip()
    date_requested_raw = request.form.get("date_requested", "").strip()

    resident_id = int(resident_id_raw) if resident_id_raw.isdigit() else None

    date_requested = None
    if date_requested_raw:
        try:
            date_requested = datetime.strptime(date_requested_raw, "%Y-%m-%d").date()
        except ValueError:
            date_requested = date_requested_raw

    candidate = ServiceRequest(
        resident_id=resident_id,
        service_type=service_type,
        description=description,
        date_requested=date_requested,
    )

    submission_service = _get_service_request_submission_service()
    result = submission_service.submit(candidate)

    if result.success:
        flash("Service Request submitted successfully.", "success")
        return redirect(url_for("main.list_service_requests"))

    form_data = {
        "resident_id": resident_id_raw,
        "service_type": service_type,
        "description": description,
        "date_requested": date_requested_raw,
    }

    global_error = None
    if getattr(result, "resident_not_found", False):
        global_error = "Resident not found."
    elif getattr(result, "resident_inactive", False):
        global_error = "Inactive Residents cannot submit new Service Requests."

    return (
        render_template(
            "service_requests/new.html",
            errors=result.errors,
            form_data=form_data,
            global_error=global_error,
        ),
        400,
    )


@main_blueprint.get("/service-requests/<int:request_id>")
def view_service_request(request_id: int):
    """Display full details of a specific service request via T11 query service."""
    query_service = _get_service_request_query_service()
    service_request = query_service.view_service_request(request_id)

    if service_request is None:
        return (
            render_template(
                "residents/not_found.html",
                message=f"Service Request with ID {request_id} was not found.",
            ),
            404,
        )

    return render_template(
        "service_requests/view.html",
        service_request=service_request,
    )


@main_blueprint.post("/service-requests/<int:request_id>/status")
def update_service_request_status(request_id: int):
    """Process controlled workflow status transitions via T10 status service."""
    action = request.form.get("action", "").strip()

    target_status = None
    if action == "start_processing":
        target_status = "In Progress"
    elif action == "complete":
        target_status = "Completed"
    elif action == "cancel":
        target_status = "Cancelled"

    if not target_status:
        flash("Invalid action requested.", "error")
        return redirect(url_for("main.list_service_requests"))

    status_service = _get_service_request_status_service()
    result = status_service.update_status(request_id, target_status)

    if result.success:
        if target_status == "In Progress":
            flash("Service Request is now In Progress.", "success")
        elif target_status == "Completed":
            flash("Service Request completed successfully.", "success")
        elif target_status == "Cancelled":
            flash("Service Request cancelled successfully.", "success")
    elif result.not_found:
        flash("Service Request not found.", "error")
    elif result.invalid_transition:
        flash("Invalid status transition requested.", "error")
    else:
        flash("Failed to update Service Request status.", "error")

    return redirect(url_for("main.list_service_requests"))