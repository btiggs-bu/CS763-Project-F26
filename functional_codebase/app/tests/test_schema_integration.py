import re
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    Table,
    UniqueConstraint,
    inspect,
    text,
)

from app.db.database import Base

pytestmark = pytest.mark.integration

ERD_TABLES = {
    "users",
    "roles",
    "user_roles",
    "threads",
    "project",
    "course",
    "lab",
    "user_threads",
    "posts",
    "comments",
    "tags",
    "threads_group",
    "threads_tag",
    "post_tag",
}

EXPECTED_FOREIGN_KEYS = {
    ("user_roles", ("user_id",), "users", ("user_id",)),
    ("user_roles", ("role_id",), "roles", ("role_id",)),
    ("threads", ("user_id",), "users", ("user_id",)),
    ("project", ("thread_id",), "threads", ("thread_id",)),
    ("course", ("thread_id",), "threads", ("thread_id",)),
    ("lab", ("thread_id",), "threads", ("thread_id",)),
    ("user_threads", ("user_id",), "users", ("user_id",)),
    ("user_threads", ("thread_id",), "threads", ("thread_id",)),
    ("posts", ("user_id",), "users", ("user_id",)),
    ("posts", ("thread_id",), "threads", ("thread_id",)),
    ("comments", ("user_id",), "users", ("user_id",)),
    ("comments", ("post_id",), "posts", ("post_id",)),
    (
        "comments",
        ("p_comment_id", "post_id"),
        "comments",
        ("comment_id", "post_id"),
    ),
    ("threads_group", ("p_thread_id",), "threads", ("thread_id",)),
    ("threads_group", ("c_thread_id",), "threads", ("thread_id",)),
    ("threads_tag", ("thread_id",), "threads", ("thread_id",)),
    ("threads_tag", ("tag_id",), "tags", ("tag_id",)),
    ("post_tag", ("post_id",), "posts", ("post_id",)),
    ("post_tag", ("tag_id",), "tags", ("tag_id",)),
}

EXPECTED_CHECKS = {
    "roles": {
        "ck_roles_role_name": ("enum", ("student", "faculty", "admin")),
    },
    "users": {
        "ck_users_username_length": ("length", "username", 3, 50),
        "ck_users_display_name_length": ("length", "display_name", 1, 100),
    },
    "threads": {
        "ck_threads_thread_type": ("enum", ("lab", "course", "project")),
        "ck_threads_restriction_level": (
            "enum",
            ("open", "restricted", "closed"),
        ),
    },
    "project": {
        "ck_project_name_length": ("length", "name", 1, 200),
        "ck_project_description_length": (
            "nullable_max",
            "description",
            5000,
        ),
    },
    "course": {
        "ck_course_name_length": ("length", "name", 1, 200),
        "ck_course_description_length": (
            "nullable_max",
            "description",
            5000,
        ),
    },
    "lab": {
        "ck_lab_name_length": ("length", "name", 1, 200),
        "ck_lab_description_length": (
            "nullable_max",
            "description",
            5000,
        ),
    },
    "posts": {
        "ck_posts_post_type": ("enum", ("announcement", "discussion")),
        "ck_posts_restriction_level": (
            "enum",
            ("inherited", "open", "restricted", "closed"),
        ),
        "ck_posts_mod_status": (
            "enum",
            ("active", "reported", "hidden_by_moderator"),
        ),
        "ck_posts_title_length": ("length", "title", 1, 200),
        "ck_posts_content_length": ("length", "content", 1, 10000),
    },
    "comments": {
        "ck_comments_restriction_level": (
            "enum",
            ("inherited", "open", "restricted", "closed"),
        ),
        "ck_comments_mod_status": (
            "enum",
            ("active", "reported", "hidden_by_moderator"),
        ),
        "ck_comments_content_length": ("length", "content", 1, 5000),
    },
    "tags": {
        "ck_tags_tag_length": ("length", "tag", 1, 50),
    },
    "threads_group": {
        "ck_threads_group_not_self": (
            "not_equal",
            "p_thread_id",
            "c_thread_id",
        ),
    },
}

EXPECTED_UNIQUES = {
    "roles": {("role_name",)},
    "users": {("username",), ("email",)},
    "user_roles": {("user_id", "role_id")},
    "user_threads": {("user_id", "thread_id")},
    "threads_group": {
        ("p_thread_id", "c_thread_id"),
        ("c_thread_id",),
    },
    "comments": {("comment_id", "post_id")},
    "tags": {("tag",)},
    "threads_tag": {("thread_id", "tag_id")},
    "post_tag": {("post_id", "tag_id")},
}

EXPECTED_INDEXES = {
    "ix_threads_user_id": ("threads", ("user_id",)),
    "ix_threads_type_restriction": (
        "threads",
        ("thread_type", "restriction_level"),
    ),
    "ix_user_roles_role_id": ("user_roles", ("role_id",)),
    "ix_user_threads_thread_id": ("user_threads", ("thread_id",)),
    "ix_posts_thread_created_at": ("posts", ("thread_id", "created_at")),
    "ix_posts_user_id": ("posts", ("user_id",)),
    "ix_posts_type_status": ("posts", ("post_type", "mod_status")),
    "ix_comments_post_created_at": ("comments", ("post_id", "created_at")),
    "ix_comments_author_id": ("comments", ("user_id",)),
    "ix_comments_parent_post": ("comments", ("p_comment_id", "post_id")),
    "ix_threads_group_parent_id": ("threads_group", ("p_thread_id",)),
    "ix_threads_tag_tag_id": ("threads_tag", ("tag_id",)),
    "ix_post_tag_tag_id": ("post_tag", ("tag_id",)),
}

EXPECTED_TRIGGERS = {
    "trg_users_updated_at",
    "trg_threads_updated_at",
    "trg_posts_updated_at",
    "trg_comments_updated_at",
    "trg_threads_subtype_consistency",
    "trg_project_subtype_consistency",
    "trg_course_subtype_consistency",
    "trg_lab_subtype_consistency",
    "trg_threads_group_type_consistency",
    "trg_threads_hierarchy_type_consistency",
    "trg_threads_delete_descendants",
}


def _assert_check_expression(expression, expected):
    kind, *arguments = expected
    normalized = "".join(expression.lower().replace('"', "").split())

    if kind == "enum":
        assert tuple(re.findall(r"'([^']*)'", expression)) == arguments[0]
    elif kind == "length":
        column, minimum, maximum = arguments
        length_expression = f"length({column}::text)"
        assert f"{length_expression}>={minimum}" in normalized
        assert f"{length_expression}<={maximum}" in normalized
    elif kind == "nullable_max":
        column, maximum = arguments
        assert f"{column}isnull" in normalized
        assert f"length({column}::text)<={maximum}" in normalized
    else:
        left, right = arguments
        assert f"{left}<>{right}" in normalized


def test_migration_matches_erd_and_model_metadata(database_engine):
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.check(config)

    inspector = inspect(database_engine)
    assert ERD_TABLES <= set(inspector.get_table_names(schema="public"))
    assert set(Base.metadata.tables) == ERD_TABLES

    actual_foreign_keys = set()
    for table_name in ERD_TABLES:
        model_table = Base.metadata.tables[table_name]
        assert {
            column["name"]
            for column in inspector.get_columns(table_name, schema="public")
        } == set(model_table.columns.keys())
        assert tuple(
            inspector.get_pk_constraint(table_name, schema="public")[
                "constrained_columns"
            ]
        ) == tuple(column.name for column in model_table.primary_key.columns)

        model_checks = {
            constraint.name
            for constraint in model_table.constraints
            if isinstance(constraint, CheckConstraint)
        }
        database_checks = {
            constraint["name"]: constraint["sqltext"]
            for constraint in inspector.get_check_constraints(
                table_name,
                schema="public",
            )
        }
        expected_checks = EXPECTED_CHECKS.get(table_name, {})
        assert set(database_checks) == set(expected_checks)
        assert set(database_checks) == model_checks
        for name, expression in expected_checks.items():
            _assert_check_expression(database_checks[name], expression)

        model_uniques = {
            tuple(column.name for column in constraint.columns)
            for constraint in model_table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        database_uniques = {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints(
                table_name,
                schema="public",
            )
        }
        assert database_uniques == EXPECTED_UNIQUES.get(table_name, set())
        assert database_uniques == model_uniques

        model_indexes = {index.name for index in model_table.indexes}
        database_indexes = {
            index["name"]
            for index in inspector.get_indexes(table_name, schema="public")
        }
        assert model_indexes <= database_indexes

        for foreign_key in inspector.get_foreign_keys(
            table_name,
            schema="public",
        ):
            actual_foreign_keys.add(
                (
                    table_name,
                    tuple(foreign_key["constrained_columns"]),
                    foreign_key["referred_table"],
                    tuple(foreign_key["referred_columns"]),
                )
            )

    assert actual_foreign_keys == EXPECTED_FOREIGN_KEYS
    actual_indexes = {
        index["name"]: (table_name, tuple(index["column_names"]))
        for table_name in ERD_TABLES
        for index in inspector.get_indexes(table_name, schema="public")
    }
    for name, expected in EXPECTED_INDEXES.items():
        assert actual_indexes[name] == expected

    with database_engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "e903d6ff7eed"
        )
        triggers = set(
            connection.execute(
                text(
                    """
                    SELECT tgname
                    FROM pg_trigger
                    WHERE NOT tgisinternal
                      AND tgrelid IN (
                          SELECT oid
                          FROM pg_class
                          WHERE relnamespace = 'public'::regnamespace
                      )
                    """
                )
            ).scalars()
        )
    assert EXPECTED_TRIGGERS <= triggers


def test_alembic_autogenerate_detects_metadata_changes(database_engine):
    probe = Table(
        "_integration_autogenerate_probe",
        Base.metadata,
        Column("id", Integer, primary_key=True),
    )
    try:
        with database_engine.connect() as connection:
            differences = compare_metadata(
                MigrationContext.configure(connection),
                Base.metadata,
            )
        assert any(
            difference[0] == "add_table"
            and difference[1].name == probe.name
            for difference in differences
        )
    finally:
        Base.metadata.remove(probe)
