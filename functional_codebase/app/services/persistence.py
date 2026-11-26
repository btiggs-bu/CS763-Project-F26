from collections.abc import Generator
from contextlib import contextmanager

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@contextmanager
def write_transaction(session: Session) -> Generator[None, None, None]:
    try:
        yield
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        sqlstate = getattr(exc.orig, "sqlstate", None)
        if sqlstate == "23505":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A record with one or more supplied unique values already exists",
            ) from exc
        if sqlstate == "23503":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A referenced record does not exist or cannot be removed",
            ) from exc
        if sqlstate in {"23502", "23514"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The submitted values violate a database constraint",
            ) from exc
        raise
