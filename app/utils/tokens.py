import jwt

from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status

from app.config import settings
from app.constants import ErrorMessage, Role
from app.schemas import TokenData


def create_access_token(data: TokenData, expires_delta: int = None):
    if expires_delta is None:
        expires_delta = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    data.exp = datetime.now(UTC) + timedelta(minutes=expires_delta)

    return jwt.encode(
        data.model_dump(),
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str, only_admin: bool = False, admin_or_manager: bool = False) -> TokenData:
    try:
        payload = TokenData.model_validate(jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        ))

        if payload:
            if only_admin and payload.role != Role.ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorMessage.INVALID_RIGHTS)

            if admin_or_manager and payload.role not in [Role.TENANT_MANAGER, Role.ADMIN]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorMessage.INVALID_RIGHTS)

            return payload

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessage.INVALID_TOKEN)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessage.TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessage.INVALID_TOKEN)
