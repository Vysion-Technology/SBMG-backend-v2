from typing import Optional

from pydantic import BaseModel


class CreateAgencyRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
