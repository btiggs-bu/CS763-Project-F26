from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import (
    CommentRestrictionLevel,
    ModerationStatus,
    PostRestrictionLevel,
    PostType,
)
from app.models.mixins import TimestampMixin


class Post(TimestampMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint(
            "post_type IN ('announcement', 'discussion')",
            name="ck_posts_post_type",
        ),
        CheckConstraint(
            "restriction_level IN ('inherited', 'open', 'restricted', 'closed')",
            name="ck_posts_restriction_level",
        ),
        CheckConstraint(
            "mod_status IN ('active', 'reported', 'hidden_by_moderator')",
            name="ck_posts_mod_status",
        ),
        CheckConstraint("length(title) BETWEEN 1 AND 200", name="ck_posts_title_length"),
        CheckConstraint("length(content) BETWEEN 1 AND 10000", name="ck_posts_content_length"),
        Index("ix_posts_thread_created_at", "thread_id", "created_at"),
        Index("ix_posts_user_id", "user_id"),
        Index("ix_posts_type_status", "post_type", "mod_status"),
    )

    post_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_type: Mapped[PostType] = mapped_column(
        SAEnum(
            PostType,
            name="post_type_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=16,
        ),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String(10000), nullable=False)
    restriction_level: Mapped[PostRestrictionLevel] = mapped_column(
        SAEnum(
            PostRestrictionLevel,
            name="post_restriction_level_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=16,
        ),
        nullable=False,
        default=PostRestrictionLevel.INHERITED,
        server_default=PostRestrictionLevel.INHERITED.value,
    )
    mod_status: Mapped[ModerationStatus] = mapped_column(
        SAEnum(
            ModerationStatus,
            name="post_mod_status_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=32,
        ),
        nullable=False,
        default=ModerationStatus.ACTIVE,
        server_default=ModerationStatus.ACTIVE.value,
    )

    author: Mapped["User"] = relationship(
        back_populates="posts",
        foreign_keys=[user_id],
    )
    thread: Mapped["Thread"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tag_assignments: Mapped[list["PostTag"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary="post_tag",
        back_populates="posts",
        viewonly=True,
    )


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "restriction_level IN ('inherited', 'open', 'restricted', 'closed')",
            name="ck_comments_restriction_level",
        ),
        CheckConstraint(
            "mod_status IN ('active', 'reported', 'hidden_by_moderator')",
            name="ck_comments_mod_status",
        ),
        CheckConstraint("length(content) BETWEEN 1 AND 5000", name="ck_comments_content_length"),
        UniqueConstraint("comment_id", "post_id", name="uq_comments_id_post"),
        Index("ix_comments_post_created_at", "post_id", "created_at"),
        Index("ix_comments_author_id", "user_id"),
        Index("ix_comments_parent_post", "p_comment_id", "post_id"),
        ForeignKeyConstraint(
            ["p_comment_id", "post_id"],
            ["comments.comment_id", "comments.post_id"],
            name="fk_comments_parent_same_post",
            ondelete="CASCADE",
        ),
    )

    comment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.post_id", ondelete="CASCADE"),
        nullable=False,
    )
    p_comment_id: Mapped[int | None] = mapped_column(nullable=True)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    restriction_level: Mapped[CommentRestrictionLevel] = mapped_column(
        SAEnum(
            CommentRestrictionLevel,
            name="comment_restriction_level_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=16,
        ),
        nullable=False,
        default=CommentRestrictionLevel.INHERITED,
        server_default=CommentRestrictionLevel.INHERITED.value,
    )
    mod_status: Mapped[ModerationStatus] = mapped_column(
        SAEnum(
            ModerationStatus,
            name="comment_mod_status_value",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            validate_strings=True,
            length=32,
        ),
        nullable=False,
        default=ModerationStatus.ACTIVE,
        server_default=ModerationStatus.ACTIVE.value,
    )

    author: Mapped["User"] = relationship(
        back_populates="comments",
        foreign_keys=[user_id],
    )
    post: Mapped[Post] = relationship(back_populates="comments")
    parent_comment: Mapped["Comment | None"] = relationship(
        back_populates="replies",
        remote_side=lambda: [Comment.comment_id, Comment.post_id],
        foreign_keys=lambda: [Comment.p_comment_id, Comment.post_id],
        overlaps="post,comments",
    )
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent_comment",
        foreign_keys=lambda: [Comment.p_comment_id, Comment.post_id],
        cascade="all, delete-orphan",
        passive_deletes=True,
        overlaps="post,comments",
    )
