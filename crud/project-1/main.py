from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from pathlib import Path


app = FastAPI()


#---------- Database setup ---------
Path("./database").mkdir(parents=True, exist_ok=True)

DATABASE_URL = "sqlite:///./database/items.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)    
Base = declarative_base()

#---------- Models ---------

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

#--------- Pydantic Schemas ---------

class ItemCreate(BaseModel):
    title: str
    description: str|None = None
    price: float
    is_active: bool|None = True

class ItemUpdate(BaseModel):
    title: str|None = None
    description: str|None = None
    price: float|None = None
    is_active: bool|None = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: str|None = None
    price: float
    is_active: bool
    
    model_config = {"from_attributes": True}

#--------- Dependency ---------

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()


@app.post("/items/", response_model=ItemResponse)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    item = Item(**item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/items", response_model=list[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()


@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item_in: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item_in.model_dump(exclude_unset=True).items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return {"detail": "Item deleted successfully"}


