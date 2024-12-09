import jwt
import requests
import base64

from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

from app.constants import *
from app.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception

    return token_data


def zitadel_check(email: str, password: str):
    try:
        token_res = requests.post(
            f'{ZITADEL_DOMAIN}/oauth/v2/token',
            headers={
                'Authorization': f'Basic {base64.b64encode(f"{ZITADEL_CLIENT_ID}:{ZITADEL_CLIENT_SECRET}".encode()).decode()}',
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
                return None

            session_res = requests.post(
                f'{ZITADEL_DOMAIN}/v2beta/sessions',
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
                    return None

                response = requests.patch(
                    f'{ZITADEL_DOMAIN}/v2beta/sessions/{session_id}',
                    headers={
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                    },
                    json={'checks': {'password': {'password': password}}}
                )

                if response.status_code == 200:
                    print('Password verified successfully.')
                    return True

        return None  # zitadel user id

    except Exception as e:
        print(f'Error while verifying password: {e}')
        return None
