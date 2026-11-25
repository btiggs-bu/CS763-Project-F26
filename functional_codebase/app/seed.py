import argparse
import logging
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import (
    Comment,
    CommentRestrictionLevel,
    Course,
    Lab,
    ModerationStatus,
    Post,
    PostRestrictionLevel,
    PostType,
    Project,
    Role,
    RoleName,
    Tag,
    Thread,
    ThreadGroup,
    ThreadRestrictionLevel,
    ThreadTag,
    ThreadType,
    User,
    UserRole,
)

logger = logging.getLogger(__name__)

SEED_USERS = (
    ("rbpdb_seed_student", "rbpdb.seed.student@example.test", "Seed Student", RoleName.STUDENT),
    ("rbpdb_seed_faculty", "rbpdb.seed.faculty@example.test", "Seed Faculty", RoleName.FACULTY),
    ("rbpdb_seed_admin", "rbpdb.seed.admin@example.test", "Seed Admin", RoleName.ADMIN),
)

SEED_LAB_NAME = "RBPDB Seed Lab"
SEED_COURSE_NAMES = ("RBPDB Seed Course A", "RBPDB Seed Course B")
SEED_PROJECT_NAMES = ("RBPDB Seed Project A", "RBPDB Seed Project B")
SEED_TAG_NAMES = ("rbpdb-seed-research", "rbpdb-seed-course", "rbpdb-seed-project")
SEED_POSTS = (
    (
        "RBPDB Seed Project Discussion",
        "rbpdb_seed_student",
        SEED_PROJECT_NAMES[0],
        PostType.DISCUSSION,
        "A small discussion fixture for API testing.",
    ),
    (
        "RBPDB Seed Course Announcement",
        "rbpdb_seed_faculty",
        SEED_COURSE_NAMES[0],
        PostType.ANNOUNCEMENT,
        "A small announcement fixture for API testing.",
    ),
)
SEED_COMMENTS = (
    (
        "discussion_root",
        SEED_POSTS[0][0],
        "rbpdb_seed_faculty",
        "A seed comment on the project discussion.",
        None,
    ),
    (
        "discussion_reply",
        SEED_POSTS[0][0],
        "rbpdb_seed_student",
        "A seed reply to the faculty comment.",
        "discussion_root",
    ),
    (
        "announcement_comment",
        SEED_POSTS[1][0],
        "rbpdb_seed_student",
        "A seed comment on the course announcement.",
        None,
    ),
)
SEED_USER_EMAILS = tuple(user[1] for user in SEED_USERS)


def seed_roles(session: Session) -> dict[RoleName, Role]:
    roles: dict[RoleName, Role] = {}
    for role_name in RoleName:
        role = session.scalar(select(Role).where(Role.role_name == role_name))
        if role is None:
            role = Role(role_name=role_name)
            session.add(role)
        roles[role_name] = role

    session.flush()
    return roles


def seed_users(session: Session, roles: dict[RoleName, Role]) -> dict[str, User]:
    users: dict[str, User] = {}
    for username, email, display_name, role_name in SEED_USERS:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                username=username,
                email=email,
                display_name=display_name,
            )
            session.add(user)
            session.flush()

        role = roles[role_name]
        if all(assignment.role_id != role.role_id for assignment in user.role_assignments):
            user.role_assignments.append(UserRole(role=role))
        users[username] = user

    session.flush()
    return users


def _get_or_create_thread(
    session: Session,
    creator: User,
    thread_type: ThreadType,
    name: str,
    description: str,
) -> Thread:
    subtype_by_type = {
        ThreadType.LAB: (Lab, "lab"),
        ThreadType.COURSE: (Course, "course"),
        ThreadType.PROJECT: (Project, "project"),
    }
    subtype_model, relationship_name = subtype_by_type[thread_type]

    thread = session.scalar(
        select(Thread)
        .join(subtype_model, subtype_model.thread_id == Thread.thread_id)
        .where(
            Thread.user_id == creator.user_id,
            Thread.thread_type == thread_type,
            subtype_model.name == name,
        )
    )
    if thread is not None:
        return thread

    thread = Thread(
        creator=creator,
        thread_type=thread_type,
        restriction_level=ThreadRestrictionLevel.RESTRICTED,
    )
    setattr(
        thread,
        relationship_name,
        subtype_model(name=name, description=description),
    )
    session.add(thread)
    session.flush()
    return thread


def _ensure_thread_group(
    session: Session,
    parent: Thread,
    child: Thread,
) -> None:
    group = session.scalar(
        select(ThreadGroup).where(
            ThreadGroup.p_thread_id == parent.thread_id,
            ThreadGroup.c_thread_id == child.thread_id,
        )
    )
    if group is None:
        session.add(
            ThreadGroup(
                parent_thread=parent,
                child_thread=child,
            )
        )


def seed_threads(session: Session, users: dict[str, User]) -> dict[str, Thread]:
    creator = users["rbpdb_seed_faculty"]
    lab = _get_or_create_thread(
        session,
        creator,
        ThreadType.LAB,
        SEED_LAB_NAME,
        "Small fixture lab for API testing.",
    )

    course_a, course_b = (
        _get_or_create_thread(
            session,
            creator,
            ThreadType.COURSE,
            name,
            "Small fixture course for API testing.",
        )
        for name in SEED_COURSE_NAMES
    )
    project_a, project_b = (
        _get_or_create_thread(
            session,
            users["rbpdb_seed_student"],
            ThreadType.PROJECT,
            name,
            "Small fixture project for API testing.",
        )
        for name in SEED_PROJECT_NAMES
    )

    _ensure_thread_group(session, lab, course_a)
    _ensure_thread_group(session, lab, course_b)
    _ensure_thread_group(session, course_a, project_a)
    _ensure_thread_group(session, course_b, project_b)
    session.flush()

    return {
        SEED_LAB_NAME: lab,
        SEED_COURSE_NAMES[0]: course_a,
        SEED_COURSE_NAMES[1]: course_b,
        SEED_PROJECT_NAMES[0]: project_a,
        SEED_PROJECT_NAMES[1]: project_b,
    }


def seed_tags(session: Session, threads: dict[str, Thread]) -> dict[str, Tag]:
    tags: dict[str, Tag] = {}
    for tag_name in SEED_TAG_NAMES:
        tag = session.scalar(select(Tag).where(Tag.tag == tag_name))
        if tag is None:
            tag = Tag(tag=tag_name)
            session.add(tag)
            session.flush()
        tags[tag_name] = tag

    assignments = (
        (threads[SEED_LAB_NAME], tags[SEED_TAG_NAMES[0]]),
        (threads[SEED_COURSE_NAMES[0]], tags[SEED_TAG_NAMES[1]]),
        (threads[SEED_PROJECT_NAMES[0]], tags[SEED_TAG_NAMES[2]]),
    )
    for thread, tag in assignments:
        assignment = session.scalar(
            select(ThreadTag).where(
                ThreadTag.thread_id == thread.thread_id,
                ThreadTag.tag_id == tag.tag_id,
            )
        )
        if assignment is None:
            session.add(ThreadTag(thread=thread, tag=tag))

    session.flush()
    return tags


def seed_posts(
    session: Session,
    users: dict[str, User],
    threads: dict[str, Thread],
) -> dict[str, Post]:
    posts: dict[str, Post] = {}
    for title, username, thread_name, post_type, content in SEED_POSTS:
        author = users[username]
        thread = threads[thread_name]
        post = session.scalar(
            select(Post).where(
                Post.thread_id == thread.thread_id,
                Post.user_id == author.user_id,
                Post.title == title,
            )
        )
        if post is None:
            post = Post(
                author=author,
                thread=thread,
                post_type=post_type,
                title=title,
                content=content,
                restriction_level=PostRestrictionLevel.INHERITED,
                mod_status=ModerationStatus.ACTIVE,
            )
            session.add(post)
            session.flush()
        posts[title] = post

    return posts


def seed_comments(
    session: Session,
    users: dict[str, User],
    posts: dict[str, Post],
) -> dict[str, Comment]:
    comments: dict[str, Comment] = {}
    for key, post_title, username, content, parent_key in SEED_COMMENTS:
        post = posts[post_title]
        author = users[username]
        parent = comments[parent_key] if parent_key is not None else None
        parent_id = parent.comment_id if parent is not None else None
        parent_filter = (
            Comment.p_comment_id == parent_id
            if parent_id is not None
            else Comment.p_comment_id.is_(None)
        )
        comment = session.scalar(
            select(Comment).where(
                Comment.post_id == post.post_id,
                Comment.user_id == author.user_id,
                Comment.content == content,
                parent_filter,
            )
        )
        if comment is None:
            comment = Comment(
                author=author,
                post=post,
                parent_comment=parent,
                content=content,
                restriction_level=CommentRestrictionLevel.INHERITED,
                mod_status=ModerationStatus.ACTIVE,
            )
            session.add(comment)
            session.flush()
        comments[key] = comment

    return comments


def clean_seed_data(session: Session) -> None:
    user_ids = select(User.user_id).where(User.email.in_(SEED_USER_EMAILS))
    for subtype, names in (
        (Project, SEED_PROJECT_NAMES),
        (Course, SEED_COURSE_NAMES),
        (Lab, (SEED_LAB_NAME,)),
    ):
        seeded_thread_ids = (
            select(Thread.thread_id)
            .join(subtype, subtype.thread_id == Thread.thread_id)
            .where(Thread.user_id.in_(user_ids), subtype.name.in_(names))
        )
        session.execute(
            delete(Thread)
            .where(Thread.thread_id.in_(seeded_thread_ids))
            .execution_options(synchronize_session=False)
        )
    session.execute(
        delete(Tag)
        .where(Tag.tag.in_(SEED_TAG_NAMES))
        .execution_options(synchronize_session=False)
    )
    session.execute(
        delete(User)
        .where(User.email.in_(SEED_USER_EMAILS))
        .execution_options(synchronize_session=False)
    )
    session.flush()


def populate_seed_data(*, reset: bool = False, clean: bool = False) -> None:
    if reset and clean:
        raise ValueError("reset and clean cannot both be enabled")

    with SessionLocal.begin() as session:
        if reset or clean:
            clean_seed_data(session)
        if clean:
            logger.info("Seed fixtures removed.")
            return

        roles = seed_roles(session)
        users = seed_users(session, roles)
        threads = seed_threads(session, users)
        tags = seed_tags(session, threads)
        posts = seed_posts(session, users, threads)
        comments = seed_comments(session, users, posts)
        logger.info(
            "Seed data ready: %d roles, %d users, %d threads, %d tags, "
            "%d posts, %d comments.",
            len(roles),
            len(users),
            len(threads),
            len(tags),
            len(posts),
            len(comments),
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Populate or reset RBPDB seed fixtures.")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--reset",
        action="store_true",
        help="remove and recreate the seed fixtures",
    )
    actions.add_argument(
        "--clean",
        action="store_true",
        help="remove seed fixtures without recreating them",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    populate_seed_data(reset=args.reset, clean=args.clean)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
