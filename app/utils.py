import base64

import requests
import jwt

from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.config import settings
from app.constants import ErrorMessage, Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: int = None):
    if expires_delta is None:
        expires_delta = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(UTC) + timedelta(minutes=expires_delta)})

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str, check_admin: bool = False):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if check_admin and payload.get("role") != Role.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorMessage.INVALID_ADMIN_RIGHTS)

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessage.TOKEN_EXPIRED)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorMessage.INVALID_TOKEN)


def hash_password(password) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def paginate_query(query, page: int, size: int):
    # In real code, add default or validation for page/size
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def verify_zitadel_credentials(email: str, password: str) -> dict | None:
    try:
        token_res = requests.post(
            f'{settings.ZITADEL_DOMAIN}/oauth/v2/token',
            headers={
                'Authorization': f'Basic {base64.b64encode(
                    f"{settings.ZITADEL_CLIENT_ID}:{settings.ZITADEL_CLIENT_SECRET}".encode()
                ).decode()}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={
                'grant_type': 'client_credentials',
                'scope': 'openid profile email urn:zitadel:iam:org:project:id:zitadel:aud',
            }
        )
        if token_res.status_code == 200:
            token = token_res.json().get('access_token')
            if not token:
                raise HTTPException(status_code=500, detail=ErrorMessage.UNKNOWN_ERROR)

            session_res = requests.post(
                f'{settings.ZITADEL_DOMAIN}/v2beta/sessions',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                json={'checks': {'user': {'loginName': email}}}
            )

            if session_res.status_code == 201:
                session_info = session_res.json()
                session_id = session_info['sessionId']
                if not session_id:
                    raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

                response = requests.patch(
                    f'{settings.ZITADEL_DOMAIN}/v2beta/sessions/{session_id}',
                    headers={
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                    },
                    json={'checks': {'password': {'password': password}}}
                )

                if response.status_code == 200:
                    response = requests.get(
                        f'{settings.ZITADEL_DOMAIN}/v2beta/sessions/{session_id}',
                        headers={
                            'Accept': 'application/json',
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json',
                        }
                    )
                    session = response.json()
                    if session and session.get('session', {}).get('factors', {}).get('user'):
                        return session['session']['factors']['user']  # zitadel user id

        raise HTTPException(status_code=401, detail=ErrorMessage.INVALID_ZITADEL_CREDENTIALS)

    except Exception as e:
        print(f'Error while verifying password: {e}')
        raise HTTPException(status_code=500, detail=ErrorMessage.UNKNOWN_ERROR)
