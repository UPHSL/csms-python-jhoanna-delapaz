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

        # Parse stored date string back into date object
        parsed_date = date.fromisoformat(row["date_requested"])

        return ServiceRequest(
            id=row["id"],
            resident_id=row["resident_id"],
            service_type=row["service_type"],
            description=row["description"],
            date_requested=parsed_date,
            status=row["status"],
        )