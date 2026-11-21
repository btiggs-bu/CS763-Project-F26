"""Initialize Alembic migration tracking.

Revision ID: 20261120_2000
Revises:
Create Date: 2026-11-20 20:27:52.961

"""
from typing import Union

revision: str = "20261120_2000"
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
