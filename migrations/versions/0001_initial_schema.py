"""Initial schema: patient/staff accounts, patient profiles, OTP tables (REQ-026)

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("online_booking_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("lock_expires_at", sa.DateTime(timezone=True)),
        sa.Column("consented_policy_version", sa.String(50)),
        sa.Column("consented_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("phone", name="uq_patient_accounts_phone"),
    )
    op.create_table(
        "patient_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("patient_accounts.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("gender", sa.String(20)),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.Text()),
        sa.Column("relationship", sa.String(50)),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_patient_profiles_account_id", "patient_profiles", ["account_id"])
    op.create_table(
        "staff_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("email", name="uq_staff_accounts_email"),
    )
    op.create_table(
        "otp_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_otp_codes_phone_created_at", "otp_codes", ["phone", "created_at"])
    op.create_table(
        "otp_counters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("send_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("phone", "window_start", name="uq_otp_counters_phone_window"),
    )


def downgrade() -> None:
    op.drop_table("otp_counters")
    op.drop_index("ix_otp_codes_phone_created_at", table_name="otp_codes")
    op.drop_table("otp_codes")
    op.drop_table("staff_accounts")
    op.drop_index("ix_patient_profiles_account_id", table_name="patient_profiles")
    op.drop_table("patient_profiles")
    op.drop_table("patient_accounts")
