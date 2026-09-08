from fastapi import FastAPI, APIRouter,Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel,Field
from models import Users, Books, Reservation
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from typing import Annotated, Optional
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt,JWTError
from router.auth import get_current_user

router = APIRouter()

class BookCreate(BaseModel):
    title : str
    author: str
    category : str
    description : str = Field(default='',max_length=200)
    price : float = Field(default=0.0, ge=0)
    total_copies: int = Field(default=1)

class BookUpdate(BaseModel):
    title : Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    category : Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    price : Optional[float] = Field(default=None)
    total_copies: Optional[int] = Field(default=None)
    available_copies : Optional[int] = Field(default=None)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post('/admin/create_book')
def create_book(user: user_dependency, db : db_dependency, new_book: BookCreate):
    if user is None or user.get('role') != "librarian":
        raise HTTPException(status_code=401, detail="Failed Authentication")
    book_model = Books(
        **new_book.model_dump(),
        available_copies = new_book.total_copies
    )
    db.add(book_model)
    db.commit()

    return JSONResponse(status_code=201, content={'message':'Book Added Successfully'})

@router.put('/admin/update_book/{book_id}')
def update_book(user: user_dependency, db : db_dependency, update_book: BookUpdate, book_id : int):
    if user is None or user.get('role') != "librarian":
        raise HTTPException(status_code=401, detail="Failed Authentication")

    book = db.query(Books).filter(Books.id == book_id).first()

    if book is None:
        raise HTTPException(status_code=404, detail="Book is not found")
    
    update_data = update_book.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)

    db.commit()
    return JSONResponse(status_code=200, content={'message':'Book Updated Successfully'})
