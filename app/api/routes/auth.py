from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import database
from app import schemas
from app.services import auth

router = APIRouter()

@router.post("/register", response_model=schemas.TokenResponse)
def register(user_data: schemas.UserRegister, db: Session = Depends(database.get_db)):
    user = auth.create_user(db, user_data.email, user_data.password)
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.TokenResponse)
def login(user_data: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_info(current_user: database.User = Depends(auth.get_current_user)):
    return current_user

