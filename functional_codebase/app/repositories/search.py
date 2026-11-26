from collections.abc import Sequence

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement


def full_text_filter(
    session: Session,
    columns: Sequence[ColumnElement[str]],
    keyword: str,
) -> ColumnElement[bool]:
    if session.get_bind().dialect.name == "postgresql":
        document = func.to_tsvector("english", func.concat_ws(" ", *columns))
        return document.bool_op("@@")(func.plainto_tsquery("english", keyword))

    pattern = f"%{keyword}%"
    return or_(*(column.ilike(pattern) for column in columns))
