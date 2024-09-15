"""Remove system account

Revision ID: d84ee690c39f
Revises: 524d39aa6fab
Create Date: 2024-09-09 13:23:20.151034

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd84ee690c39f'
down_revision: Union[str, None] = '524d39aa6fab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    users = sa.sql.table(
        "users",
        sa.sql.column("id", sa.Integer),
        sa.sql.column("alternative_id", sa.String),
        sa.sql.column("enabled", sa.Boolean),
        sa.sql.column("locale", sa.String),
        sa.sql.column("name", sa.String),
        sa.sql.column("right", sa.Integer),
        sa.sql.column("otp_confirmed", sa.Boolean),
    )
    op.execute(
        users.delete().where(users.c.id == 0)
    )


def downgrade() -> None:
    users = sa.sql.table(
        "users",
        sa.sql.column("id", sa.Integer),
        sa.sql.column("alternative_id", sa.String),
        sa.sql.column("enabled", sa.Boolean),
        sa.sql.column("locale", sa.String),
        sa.sql.column("name", sa.String),
        sa.sql.column("right", sa.Integer),
        sa.sql.column("otp_confirmed", sa.Boolean),
    )
    op.bulk_insert(
        users,
        [
            {
                "id": 0,
                "alternative_id": 0,
                "enabled": False,
                "locale": "en",
                "name": "system",
                "right": 8,
                "otp_confirmed": False,
            }
        ],
    )
