"""Resident Model

The Resident domain model will be implemented in CSMS-201.
"""

# The class for the model---------------------------------
class Resident:
    def __init__( # setup func
        self,
        # parameters 
        id: int,
        first_name: str,
        last_name: str,
        address: str,
        contact_number: str,
        email: str,
        status: str = "Active"
    ):
        # Save each information piece onto the object so it can be accessed later.
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.address = address
        self.contact_number = contact_number
        self.email = email
        self.status = status