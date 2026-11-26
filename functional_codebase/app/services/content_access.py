from fastapi import HTTPException, status

from app.models.enums import RoleName, ThreadRestrictionLevel
from app.models.thread import Thread
from app.models.user import User


def has_staff_role(user: User) -> bool:
    roles = {role.role_name for role in user.roles}
    return RoleName.FACULTY in roles or RoleName.ADMIN in roles


def require_content_access(
    user: User,
    restriction_level: ThreadRestrictionLevel,
    is_thread_member: bool,
) -> None:
    roles = {role.role_name for role in user.roles}
    if restriction_level == ThreadRestrictionLevel.OPEN:
        return
    if restriction_level == ThreadRestrictionLevel.CLOSED:
        if RoleName.ADMIN in roles:
            return
    elif is_thread_member or RoleName.FACULTY in roles or RoleName.ADMIN in roles:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The user is not permitted to access content with this restriction",
    )


def require_thread_access(
    user: User,
    thread: Thread,
    is_thread_member: bool,
) -> None:
    require_content_access(user, thread.restriction_level, is_thread_member)
