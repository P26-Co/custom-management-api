import base64

import requests

from fastapi import HTTPException

from app.config import settings
from app.constants import ErrorMessage


def get_zitadel_access_token() -> str:
    res = requests.post(
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
    if res.status_code == 200:
        token = res.json().get('access_token')
        if not token:
            raise HTTPException(status_code=500, detail=ErrorMessage.INVALID_TOKEN)
        return token
    raise HTTPException(status_code=500, detail=ErrorMessage.INVALID_TOKEN)


def verify_zitadel_credentials(email: str, password: str) -> dict | None:
    token = get_zitadel_access_token()

    res = requests.post(
        f'{settings.ZITADEL_DOMAIN}/v2beta/sessions',
        headers={
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        json={'checks': {'user': {'loginName': email}}}
    )

    if res.status_code == 201:
        session_info = res.json()
        session_id = session_info.get('sessionId')
        if not session_id:
            raise HTTPException(status_code=404, detail=ErrorMessage.USER_NOT_FOUND)

        res = requests.patch(
            f'{settings.ZITADEL_DOMAIN}/v2beta/sessions/{session_id}',
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            json={'checks': {'password': {'password': password}}}
        )

        if res.status_code == 200:
            res = requests.get(
                f'{settings.ZITADEL_DOMAIN}/v2beta/sessions/{session_id}',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                }
            )
            session = res.json()
            if session and session.get('session', {}).get('factors', {}).get('user'):
                return session['session']['factors']['user']  # zitadel user id

    if res.json().get('message'):
        raise HTTPException(status_code=401, detail=res.json().get('message'))
    else:
        return None


def get_zitadel_users(offset: int, limit: int, tenant_id: int):
    """
    Call Zitadel API to retrieve users for the given page.
    """
    response = requests.post(
        f'{settings.ZITADEL_DOMAIN}/v2beta/users',
        headers={
            'Accept': 'application/json',
            'Authorization': f'Bearer {get_zitadel_access_token()}',
            'Content-Type': 'application/json',
        },
        json={
            "query": {
                "offset": offset,
                "limit": limit
            },
            "queries": [
                {
                    "organizationIdQuery": {
                        "organizationId": tenant_id
                    }
                }
            ]
        }
    )
    if response.status_code == 200:
        return response.json()

    raise HTTPException(status_code=500, detail=response.json().get('message'))


def get_zitadel_tenants(offset: int, limit: int):
    """
    Call Zitadel API to retrieve orgs for the given page.
    """
    response = requests.post(
        f'{settings.ZITADEL_DOMAIN}/admin/v1/orgs/_search',
        headers={
            'Accept': 'application/json',
            'Authorization': f'Bearer {get_zitadel_access_token()}',
            'Content-Type': 'application/json',
        },
        json={
            "query": {
                "offset": offset,
                "limit": limit
            }
        }
    )
    if response.status_code == 200:
        return response.json()

    raise HTTPException(status_code=500, detail=response.json().get('message'))
