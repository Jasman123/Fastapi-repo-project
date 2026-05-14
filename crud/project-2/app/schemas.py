from pydantic import BaseModel, Field
from datetime import datetime


class ItemCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str|None = None
    price: float = Field(..., gt=0)
    is_active: bool|None = True 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime|None = None

class ItemUpdate(BaseModel):
    title: str|None = Field(None, max_length=200)
    description: str|None = None
    price: float|None = Field(None, gt=0)
    is_active: bool|None = None
    created_at: datetime
    updated_at: datetime|None = Field(default_factory=datetime.utcnow)

class ItemResponse(BaseModel):
    id: int
    title: str
    description: str|None = None
    price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
