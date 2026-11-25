from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        CheckConstraint("length(tag) BETWEEN 1 AND 50", name="ck_tags_tag_length"),
    )

    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tag: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    thread_assignments: Mapped[list["ThreadTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    threads: Mapped[list["Thread"]] = relationship(
        secondary="threads_tag",
        back_populates="tags",
        viewonly=True,
    )
    post_assignments: Mapped[list["PostTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    posts: Mapped[list["Post"]] = relationship(
        secondary="post_tag",
        back_populates="tags",
        viewonly=True,
    )


class ThreadTag(Base):
    __tablename__ = "threads_tag"
    __table_args__ = (
        UniqueConstraint("thread_id", "tag_id", name="uq_threads_tag_thread_tag"),
        Index("ix_threads_tag_tag_id", "tag_id"),
    )

    thread_tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        nullable=False,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        nullable=False,
    )

    thread: Mapped["Thread"] = relationship(back_populates="tag_assignments")
    tag: Mapped[Tag] = relationship(back_populates="thread_assignments")


class PostTag(Base):
    __tablename__ = "post_tag"
    __table_args__ = (
        UniqueConstraint("post_id", "tag_id", name="uq_post_tag_post_tag"),
        Index("ix_post_tag_tag_id", "tag_id"),
    )

    post_tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.post_id", ondelete="CASCADE"),
        nullable=False,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.tag_id", ondelete="CASCADE"),
        nullable=False,
    )

    post: Mapped["Post"] = relationship(back_populates="tag_assignments")
    tag: Mapped[Tag] = relationship(back_populates="post_assignments")
