from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import models
from models import Books, Users, Reservation, IssueRecords
from database import SessionLocal, engine
from fastapi.responses import JSONResponse
from router import admin, auth
from router.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# origins = [
#     "http://localhost:5173",
#     "http://localhost:5174",
#     "http://127.0.0.1:5173",
#     "http://127.0.0.1:5174",
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(admin.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@app.get('/books/all')
def get_all_books(db : db_dependency):

    # if user is None:
    #     raise HTTPException(status_code=401, detail='Failed Authentication')
    books = db.query(Books).all()
    return books


@app.get('/book/{book_id}')
def get_spacific_book(user : user_dependency, db : db_dependency, book_id: int):

    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    book = db.query(Books).filter(Books.id == book_id).first()
    return book

@app.post('/reserve/{book_id}')
def reserve_book(user: user_dependency, db: db_dependency, book_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    book = db.query(Books).filter(Books.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail='Book not found')
    reservation_model = Reservation(
        book_id = book_id,
        user_id = user.get('id'),
        status = 'panding'
    )

    db.add(reservation_model)
    db.commit()

    return JSONResponse(status_code=201, content={'message': 'Book reserved Successfully'})


@app.delete('/reserve/cancel/{reservation_id}')
def cancel_reservation(user: user_dependency, db: db_dependency, reservation_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=404, detail='Reservation not found')
    
    reservation.status = 'cancelled'
    db.commit()

    return JSONResponse(status_code=201, content={'message': 'Reservation cancelled Successfully'})

@app.get('/reserve/my')
def myreservation(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    reservations = db.query(Reservation).filter(Reservation.user_id == user.get('id')).all()
    return reservations

@app.get('/issues/my')
def my_issued_books(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Failed Authentication')
    
    Issues = db.query(IssueRecords).filter(
        IssueRecords.user_id == user.get('id'),
        IssueRecords.status == 'issued').all()
    return Issues