from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import RoleName
from app.models.user import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Role)

    def get_by_names(self, role_names: Sequence[RoleName]) -> list[Role]:
        if not role_names:
            return []
        statement = select(Role).where(Role.role_name.in_(role_names))
        return list(self.session.scalars(statement).all())
