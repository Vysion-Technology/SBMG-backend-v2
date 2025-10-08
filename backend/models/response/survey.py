from datetime import datetime

from pydantic import BaseModel


class FormResponse(BaseModel):
    id: int
    title: str
    role: str
class FilledFormResponse(BaseModel):
    id: int
    title: str

class AssignmentResponse(BaseModel):
    id: int
    form_id: int
    assigned_at: datetime
    completed: bool