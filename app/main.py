from datetime import timedelta

from fastapi import FastAPI, status, HTTPException, Depends
from sqlalchemy.orm import Session

from app import models
from app import constants
from app import schemas
from app import services
from app.database import Base, engine, SessionLocal

Base.metadata.create_all(engine)  # Create the database

app = FastAPI(
    title="Custom Manager | AppSavi",
    root_path="/api/v1",
    version="1.0.0"
)


# Helper function to get the database session
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.get("/")
async def home():
    return {"message": "Welcome to AppSavi"}


@app.post("/email-password", response_model=schemas.Token, status_code=status.HTTP_200_OK)
async def login_password(data: schemas.LoginPassword, session: Session = Depends(get_session)):
    zitadel = services.zitadel_check(data.email, data.password)
    if not zitadel:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {data.email}")

    user = session.query(models.User).filter(models.User.email == data.email).first()
    if user is None:
        user = models.User(
            email=data.email,
            device_id=data.device_id
        )
        session.add(user)

    session.commit()
    session.refresh(user)

    # Create token here
    access_token = services.create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return schemas.Token(access_token=access_token, token_type="bearer", is_pin_allowed=bool(user.pin))


@app.post("/email-pin", response_model=schemas.Token, status_code=status.HTTP_200_OK)
async def login_pin(data: schemas.LoginPin, session: Session = Depends(get_session)):
    user = session.query(models.User).filter(
        models.User.email == data.email,
        models.User.pin == data.pin
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {data.email}")

    # Create token here
    access_token = services.create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return schemas.Token(access_token=access_token, token_type="bearer", is_pin_allowed=bool(user.pin))


@app.post("/set-pin", response_model=schemas.Token)
async def set_pin(
        data: schemas.SetPin, session: Session = Depends(get_session), user=Depends(services.get_current_user)
):
    user_db = session.query(models.User).filter(models.User.email == user.email).first()
    if user_db:
        user_db.pin = data.pin
        session.commit()

    if not user_db:
        raise HTTPException(status_code=401, detail=f"Unauthorized")

    access_token = services.create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return schemas.Token(access_token=access_token, token_type="bearer", is_pin_allowed=bool(user_db.pin))
