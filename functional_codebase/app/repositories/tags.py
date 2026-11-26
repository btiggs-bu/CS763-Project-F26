from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Tag)

    def get_or_create_by_names(self, names: Sequence[str]) -> list[Tag]:
        if not names:
            return []

        tags = list(self.session.scalars(select(Tag).where(Tag.tag.in_(names))).all())
        tags_by_name = {tag.tag: tag for tag in tags}
        missing = [Tag(tag=name) for name in names if name not in tags_by_name]
        if missing:
            self.session.add_all(missing)
            self.session.flush()
            tags_by_name.update({tag.tag: tag for tag in missing})
        return [tags_by_name[name] for name in names]
