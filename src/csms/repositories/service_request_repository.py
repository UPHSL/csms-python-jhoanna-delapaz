'''
# Ticket T09: Service Request Repository (SQLite Persistence)
# manages real SQLite persistence and retrieval for Service Requests

'''

import sqlite3
from datetime import date
from typing import Optional
from src.csms.models.service_request import ServiceRequest


class ServiceRequestRepository:

    def __init__(self, db_path: str = "csms.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """creates the service_requests table if it does not already exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS service_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resident_id INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                description TEXT NOT NULL,
                date_requested TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (resident_id) REFERENCES residents (id)
            )
            """
        )
        conn.commit()
        conn.close()

    # T11: Helper method to map SQLite rows to ServiceRequest instances cleanly
    def _map_row_to_service_request(self, row: sqlite3.Row) -> ServiceRequest:
        parsed_date = date.fromisoformat(row["date_requested"])
        return ServiceRequest(
            id=row["id"],
            resident_id=row["resident_id"],
            service_type=row["service_type"],
            description=row["description"],
            date_requested=parsed_date,
            status=row["status"],
        )

    def save(self, service_request: ServiceRequest) -> ServiceRequest:
        """continues a valid Service Request and attaches the auto-generated ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # date format as YYYY-MM-DD string 
        date_str = (
            service_request.date_requested.isoformat()
            if isinstance(service_request.date_requested, date)
            else str(service_request.date_requested)
        )

        cursor.execute(
            """
            INSERT INTO service_requests (resident_id, service_type, description, date_requested, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                service_request.resident_id,
                service_request.service_type,
                service_request.description,
                date_str,
                service_request.status,
            ),
        )

        conn.commit()
        service_request.id = cursor.lastrowid  # Retrieve auto-generated ID
        conn.close()

        return service_request

    def find_by_id(self, request_id: int) -> Optional[ServiceRequest]:
        """Retrieves the persisted Service Request by its auto-generated ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, resident_id, service_type, description, date_requested, status
            FROM service_requests
            WHERE id = ?
            """,
            (request_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return self._map_row_to_service_request(row)

    # T10: updates only the status field of a persisted Service Request
    def update_status(self, request_id: int, new_status: str) -> None:
        """updates the status column in SQLite using parameterized query"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE service_requests
            SET status = ?
            WHERE id = ?
            """,
            (new_status, request_id),
        )

        conn.commit()
        conn.close()

    # T11: Persistent listing, partial text search, status filtering, and deterministic ordering
    def find_all(self) -> list[ServiceRequest]:
        """Retrieves all service requests ordered by dateRequested DESC, then id DESC."""
        return self.search(search_term=None, status_filter=None)

    def search(
        self,
        search_term: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> list[ServiceRequest]:
        """
        Queries persisted Service Requests with optional partial text matching across 
        service_type OR description and optional status filtering.
        Uses parameterized SQL queries and orders results by date_requested DESC, id DESC.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, resident_id, service_type, description, date_requested, status
            FROM service_requests
        """
        conditions = []
        params = []

        # Text search matching serviceType OR description (case-insensitive partial match via LIKE)
        if search_term:
            conditions.append("(service_type LIKE ? OR description LIKE ?)")
            wildcard_term = f"%{search_term}%"
            params.extend([wildcard_term, wildcard_term])

        # Filter by specific status
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Required ordering: dateRequested DESC, then id DESC
        query += " ORDER BY date_requested DESC, id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._map_row_to_service_request(row) for row in rows]