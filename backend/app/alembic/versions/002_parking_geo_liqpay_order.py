"""parking geo + liqpay order id on payments

Revision ID: 002
Revises: 001
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "parkings",
        sa.Column("latitude", sa.Float(), nullable=False, server_default="50.4501"),
    )
    op.add_column(
        "parkings",
        sa.Column("longitude", sa.Float(), nullable=False, server_default="30.5234"),
    )
    op.alter_column("parkings", "latitude", server_default=None)
    op.alter_column("parkings", "longitude", server_default=None)

    op.add_column("payments", sa.Column("liqpay_order_id", sa.String(128), nullable=True))
    op.create_index("ix_payments_liqpay_order_id", "payments", ["liqpay_order_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_payments_liqpay_order_id", table_name="payments")
    op.drop_column("payments", "liqpay_order_id")
    op.drop_column("parkings", "longitude")
    op.drop_column("parkings", "latitude")
