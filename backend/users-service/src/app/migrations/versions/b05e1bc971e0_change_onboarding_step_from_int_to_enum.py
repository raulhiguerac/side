"""Change onboarding step from int to enum

Revision ID: b05e1bc971e0
Revises: 45b16114b3c6
Create Date: 2026-02-03 14:22:31.863344

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

ENUM_NAME = "onboardingstep"
ENUM_VALUES = ("intent", "city", "neighborhood", "done")

# revision identifiers, used by Alembic.
revision: str = 'b05e1bc971e0'
down_revision: Union[str, Sequence[str], None] = '45b16114b3c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    onboarding_enum = postgresql.ENUM(*ENUM_VALUES, name=ENUM_NAME)
    onboarding_enum.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "accounts",
        "onboarding_step",
        existing_type=sa.INTEGER(),
        type_=onboarding_enum,
        existing_nullable=False,
        postgresql_using="""
        CASE onboarding_step
          WHEN 0 THEN 'intent'
          WHEN 1 THEN 'city'
          WHEN 2 THEN 'neighborhood'
          WHEN 3 THEN 'done'
        END::onboardingstep
        """,
    )

    op.alter_column(
        "accounts",
        "onboarding_step",
        server_default=sa.text("'intent'")
    )


def downgrade() -> None:
    onboarding_enum = postgresql.ENUM(*ENUM_VALUES, name=ENUM_NAME)

    op.alter_column(
        "accounts",
        "onboarding_step",
        server_default=None
    )

    op.alter_column(
        "accounts",
        "onboarding_step",
        existing_type=onboarding_enum,
        type_=sa.INTEGER(),
        existing_nullable=False,
        postgresql_using="""
        CASE onboarding_step
          WHEN 'intent' THEN 0
          WHEN 'city' THEN 1
          WHEN 'neighborhood' THEN 2
          WHEN 'done' THEN 3
        END
        """,
    )

    onboarding_enum.drop(op.get_bind(), checkfirst=True)