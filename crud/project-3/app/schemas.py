from pydantic import BaseModel, Field
from datetime import datetime

class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str|None = None
    price: float = Field(..., gt=0)
    is_active: bool|None = True

class ItemUpdate(BaseModel):
    title: str|None = Field(None, min_length=1, max_length=200)
    description: str|None = Field(None, max_length=1000)
    price: float|None = Field(None, gt=0)
    is_active: bool|None = None


class ItemResponse(BaseModel):
    id: int
    title: str
    description: str|None = None
    price: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

class ItemListResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    page: int
    size: int

    