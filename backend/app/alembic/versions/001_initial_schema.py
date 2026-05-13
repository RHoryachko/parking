"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-04-30

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    userrole = postgresql.ENUM("client", "worker", "admin", name="userrole", create_type=True)
    workmode = postgresql.ENUM("manual", "ai", name="workmode", create_type=True)
    spotstatus = postgresql.ENUM("free", "reserved", "occupied", "inactive", name="spotstatus", create_type=True)
    bookingstatus = postgresql.ENUM(
        "created", "paid", "canceled", "expired", "used", name="bookingstatus", create_type=True
    )
    sessionstatus = postgresql.ENUM("active", "completed", name="sessionstatus", create_type=True)
    paymentstatus = postgresql.ENUM(
        "pending", "paid", "failed", "refunded", name="paymentstatus", create_type=True
    )
    barrieraction = postgresql.ENUM("open", "close", name="barrieraction", create_type=True)

    userrole.create(bind, checkfirst=True)
    workmode.create(bind, checkfirst=True)
    spotstatus.create(bind, checkfirst=True)
    bookingstatus.create(bind, checkfirst=True)
    sessionstatus.create(bind, checkfirst=True)
    paymentstatus.create(bind, checkfirst=True)
    barrieraction.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "parkings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("address", sa.String(512), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("work_mode", workmode, nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_parkings_city", "parkings", ["city"], unique=False)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plate_number", sa.String(32), nullable=False),
        sa.Column("brand", sa.String(128), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("color", sa.String(64), nullable=True),
    )
    op.create_index("ix_vehicles_plate_number", "vehicles", ["plate_number"], unique=False)
    op.create_unique_constraint("uq_vehicles_plate_number", "vehicles", ["plate_number"])

    op.create_table(
        "parking_spots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parking_id", sa.Integer(), sa.ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("status", spotstatus, nullable=False, server_default="free"),
    )
    op.create_index("ix_parking_spots_parking_id", "parking_spots", ["parking_id"], unique=False)
    op.create_unique_constraint("uq_spot_parking_code", "parking_spots", ["parking_id", "code"])

    op.create_table(
        "tariffs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parking_id", sa.Integer(), sa.ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_per_hour", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_tariffs_parking_id", "tariffs", ["parking_id"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("parking_id", sa.Integer(), sa.ForeignKey("parkings.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("spot_id", sa.Integer(), sa.ForeignKey("parking_spots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tariff_id", sa.Integer(), sa.ForeignKey("tariffs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("planned_start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planned_end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", bookingstatus, nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("entry_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sessionstatus, nullable=False, server_default="active"),
    )
    op.create_unique_constraint("uq_sessions_booking_id", "sessions", ["booking_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", paymentstatus, nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "barrier_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parking_id", sa.Integer(), sa.ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("worker_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", barrieraction, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_barrier_logs_parking_id", "barrier_logs", ["parking_id"], unique=False)

    op.create_table(
        "ai_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parking_id", sa.Integer(), sa.ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recognized_plate", sa.String(64), nullable=False),
        sa.Column("access_allowed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_logs_parking_id", "ai_logs", ["parking_id"], unique=False)

    op.create_table(
        "worker_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("worker_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parking_id", sa.Integer(), sa.ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_unique_constraint("uq_worker_parking_assignment", "worker_assignments", ["worker_id", "parking_id"])


def downgrade() -> None:
    op.drop_table("worker_assignments")
    op.drop_table("ai_logs")
    op.drop_table("barrier_logs")
    op.drop_table("payments")
    op.drop_table("sessions")
    op.drop_table("bookings")
    op.drop_table("tariffs")
    op.drop_table("parking_spots")
    op.drop_table("vehicles")
    op.drop_table("parkings")
    op.drop_table("users")

    bind = op.get_bind()
    postgresql.ENUM(name="barrieraction").drop(bind, checkfirst=True)
    postgresql.ENUM(name="paymentstatus").drop(bind, checkfirst=True)
    postgresql.ENUM(name="sessionstatus").drop(bind, checkfirst=True)
    postgresql.ENUM(name="bookingstatus").drop(bind, checkfirst=True)
    postgresql.ENUM(name="spotstatus").drop(bind, checkfirst=True)
    postgresql.ENUM(name="workmode").drop(bind, checkfirst=True)
    postgresql.ENUM(name="userrole").drop(bind, checkfirst=True)
