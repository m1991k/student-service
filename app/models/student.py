from pydantic import BaseModel, Field
from typing import Optional

class Student(BaseModel):
    id: Optional[str] = None
    name: str
    age: int
    email: str = Field(...)
