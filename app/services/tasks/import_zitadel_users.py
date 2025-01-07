from sqlalchemy.orm import Session

from app.constants import (
    TaskStatusCode,
    TaskMessage
)
from app.schemas import (
    ZitadelTenantSchema,
    ZitadelUserSchema
)
from app.services.task_status import update_task_status
from app.services.zitadel_tenant import create_zitadel_tenant
from app.services.zitadel_user import create_zitadel_user
from app.utils import (
    get_zitadel_tenants,
    get_zitadel_users
)


def import_zitadel_users(db: Session, task_id: str):
    """
    Fetching users from Zitadel with pagination,
    storing them in the DB, and updating import status.
    """
    # 1. Mark the import as IN_PROGRESS
    update_task_status(
        db, task_id, task_status=TaskStatusCode.IN_PROGRESS, message=TaskMessage.IMPORTING_TENANTS
    )

    try:
        limit = 1000
        tenants_imported_count = 0
        tenants_offset = 0

        while True:
            tenants = get_zitadel_tenants(offset=tenants_offset, limit=limit)

            result = tenants.get("result", [])
            if not result:
                break

            for tenant in result:
                tenant_db = create_zitadel_tenant(db, ZitadelTenantSchema(
                    zitadel_tenant_id=tenant.get("id"), name=tenant.get("name"), id='SYSTEM'
                ))
                tenants_imported_count += 1
                update_task_status(db, task_id, message=f'Imported {tenants_imported_count} tenants')

                users_imported_count = 0
                users_offset = 0
                while True:
                    users = get_zitadel_users(offset=users_offset, limit=limit, tenant_id=tenant.get("id"))

                    result = users.get("result", [])
                    if not result:
                        break

                    for user in result:
                        create_zitadel_user(db, ZitadelUserSchema(
                            zitadel_user_id=user.get("userId"),
                            tenant_id=tenant_db.id,
                            name=user.get("human", {}).get("profile", {}).get("displayName"),
                            email=user.get("human", {}).get("email", {}).get("email"),
                            id='SYSTEM'
                        ))
                        users_imported_count += 1
                        update_task_status(db, task_id, message=f'Imported {users_imported_count} users')

                    users_offset += limit

            tenants_offset += limit

        # Mark as COMPLETED
        update_task_status(db, task_id, task_status=TaskStatusCode.COMPLETED, message=f'Imported!')

    except Exception as e:
        update_task_status(db, task_id, task_status=TaskStatusCode.FAILED, message=str(e))
